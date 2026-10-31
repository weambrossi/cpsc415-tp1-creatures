"""Critic-checker: a vision model critiques each image, plain code checks the critique (spec.md, C1-C12).

    python -m app.critic images/joud/manifest.json                                   # needs OPENROUTER_API_KEY
    python -m app.critic images/joud/manifest.json --model xiaomi/mimo-v2.6-flash --out images/joud/critique-mimo.json
    python -m app.critic --compare images/joud/critique.json images/joud/critique-mimo.json   # no key

The model gets each image's requirements as a yes/no checklist and must answer in JSON. The code
then decides: every requirement answered with a real true/false, none invented, each one met. The
name in the banner is read by a second, narrower question and compared in code; the checklist's
own opinion of the banner never overrides that. The server calls critique_one for a single image.
"""
import argparse
import base64
import json
import os
import re
import string
import sys
from pathlib import Path

DEFAULT_MODEL = "minimax/minimax-m3"
# Hidden reasoning is a per-model setting; the SDK takes it as an effort level.
REASONING = {"xiaomi/mimo-v2.6-flash": {"effort": "none"}}

CHECKLIST_PROMPT = """You are checking a generated image against the prompt that produced it.
Prompt: {prompt}

Answer every item below with true or false, strictly from what is visible in the image.
Reply with one JSON object and nothing else:
{{"checks": [{{"requirement": "<item text, copied exactly>", "met": true, "evidence": "<one short sentence>"}}, ...]}}

Items:
{items}"""

TEXT_PROMPT = ("Write the largest piece of text in this image exactly as printed, character for character. "
               "Reply with that text only.")

NOT_JSON = "critique was not the JSON checklist that was asked for"


# ---------- plain code: no model, no key ----------

def extract_json(text: str | None) -> dict | None:
    """The JSON object inside a reply, or None. Models wrap JSON in fences or prose (C1, C2)."""
    if not isinstance(text, str) or not text:
        return None
    decoder, found = json.JSONDecoder(), []
    for start in (i for i, ch in enumerate(text) if ch == "{"):
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            if "checks" in obj:
                return obj           # the checklist, even with other braces in the prose around it
            found.append(obj)
    return found[0] if found else None


def check(requirements: list[str], critique: dict | None) -> dict:
    """Compare the critic's checklist with the requirements (C1, C3-C6). Only what the code can say for sure."""
    if critique is None or not isinstance(critique.get("checks"), list):
        return {"ok": False, "problems": [NOT_JSON], "unmet": [], "missing": list(requirements), "extra": []}
    answers: dict[str, list] = {}
    asked_as: dict[str, str] = {}
    for c in critique["checks"]:
        if isinstance(c, dict) and isinstance(c.get("requirement"), str):
            key = _norm(c["requirement"])
            answers.setdefault(key, []).append(c.get("met"))
            asked_as.setdefault(key, c["requirement"])
    wanted = {_norm(r): r for r in requirements}
    missing, unmet = [], []
    for key, req in wanted.items():
        mets = answers.get(key, [])
        # C5: only a real JSON boolean counts, and two different verdicts for one item are no answer at all.
        if not mets or any(not isinstance(m, bool) for m in mets) or len(set(mets)) > 1:
            missing.append(req)
        elif mets[0] is False:
            unmet.append(req)
    extra = [asked_as[k] for k in answers if k not in wanted]
    problems = ([f"not answered: {r}" for r in missing] + [f"answered but not asked: {r}" for r in extra]
                + [f"unmet: {r}" for r in unmet])
    return {"ok": not problems, "problems": problems, "unmet": unmet, "missing": missing, "extra": extra}


def text_matches(expected: str, read: str | None) -> bool:
    """The name the model read equals the one asked for, ignoring case and surrounding punctuation (C7)."""
    if not read:
        return False
    return _strip_text(read) == _strip_text(expected) != ""


def disagreements(a: list[dict], b: list[dict]) -> list[dict]:
    """Images where two critique files differ on any requirement or the name read, or exist in only one (C10)."""
    by_a, by_b = {e["name"]: e for e in a}, {e["name"]: e for e in b}
    out = []
    for name in list(by_a) + [n for n in by_b if n not in by_a]:
        ea, eb = by_a.get(name), by_b.get(name)
        if ea is None or eb is None:
            out.append({"name": name, "diffs": [{"requirement": "<image>", "a": ea is not None, "b": eb is not None}]})
            continue
        va, vb = _verdicts(ea), _verdicts(eb)
        diffs = []
        for key in sorted(set(va) | set(vb)):
            text, met_a = va.get(key, (None, None))
            text_b, met_b = vb.get(key, (None, None))
            if met_a != met_b:
                diffs.append({"requirement": text or text_b, "a": met_a, "b": met_b})
        if _strip_text(ea.get("text_read") or "") != _strip_text(eb.get("text_read") or ""):
            diffs.append({"requirement": "<text read>", "a": ea.get("text_read"), "b": eb.get("text_read")})
        if diffs:
            out.append({"name": name, "diffs": diffs})
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _strip_text(s: str) -> str:
    return s.strip().strip(string.punctuation + "“”‘’ \n\t").upper()


def _verdicts(entry: dict) -> dict:
    checks = (entry.get("critique") or {}).get("checks") or []
    # Model-written text: skip entries without a string requirement, and match loosely (C6).
    return {_norm(c["requirement"]): (c["requirement"], c.get("met")) for c in checks
            if isinstance(c, dict) and isinstance(c.get("requirement"), str)}


# ---------- the billed part ----------

def ask(client, model: str, image_bytes: bytes, media_type: str, question: str,
        max_tokens: int = 1500) -> tuple[str | None, dict]:
    """One vision call: the question plus the image as a data URL, through the chat endpoint."""
    data = base64.b64encode(image_bytes).decode()
    kwargs = {"reasoning": REASONING[model]} if model in REASONING else {}
    c = client.chat.send(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}}]}], **kwargs)
    usage = {"in": c.usage.prompt_tokens, "out": c.usage.completion_tokens,
             "cost": getattr(c.usage, "cost", None)} if c.usage else {"cost": None}
    if not c.choices:
        return None, {**usage, "finish": None}
    usage["finish"] = c.choices[0].finish_reason      # "length" means the budget ran out mid-answer (C1)
    content = c.choices[0].message.content
    return (content if isinstance(content, str) else None), usage


def critique_one(client, model: str, image_bytes: bytes, media_type: str, prompt: str,
                 requirements: list[str], expected_text: str | None = None) -> dict:
    """Checklist call, then the name call if a name is expected; both answers checked in code (C7, C8)."""
    items = "\n".join(f"- {r}" for r in requirements)
    raw, usage = ask(client, model, image_bytes, media_type, CHECKLIST_PROMPT.format(prompt=prompt, items=items))
    # C1: a reply cut off at the token limit is a failed critique, even if what arrived parses.
    critique = extract_json(raw) if usage.get("finish") != "length" else None
    result = {"model": model, "critique": critique, "raw": raw, "usage": usage,
              "check": check(requirements, critique)}
    problems = list(result["check"]["problems"])
    if expected_text:
        read, usage_text = ask(client, model, image_bytes, media_type, TEXT_PROMPT, max_tokens=400)
        result["text_read"] = (read or "").strip()
        result["text_matches"] = text_matches(expected_text, read)
        result["usage_text"] = usage_text
        if not result["text_matches"]:
            problems.append(f"name reads {result['text_read']!r}, expected {expected_text!r}")
    result["passes"] = not problems
    result["problems"] = problems
    return result


def critique_set(client, model: str, manifest_path: Path, out_path: Path) -> list[dict]:
    """One critique per manifest image; the file is rewritten after each image (C9)."""
    manifest = json.loads(manifest_path.read_text())
    results = []
    for entry in manifest:
        try:
            r = critique_one(client, model, (manifest_path.parent / entry["file"]).read_bytes(),
                             entry["media_type"], entry["prompt"], entry["requirements"],
                             entry.get("expected_text"))
        except Exception as e:  # noqa: BLE001  one image's API error must not lose the others (C9)
            r = {"model": model, "critique": None, "raw": None, "usage": {}, "error": f"{type(e).__name__}: {e}",
                 "check": check(entry["requirements"], None), "passes": False,
                 "problems": [f"critique call failed: {type(e).__name__}: {e}"]}
        results.append({"name": entry["name"], **r})
        out_path.write_text(json.dumps(results, indent=2) + "\n")
        verdict = "pass" if r["passes"] else "FAIL: " + "; ".join(r["problems"])
        print(f"{entry['name']}: {verdict}  [cost ${r['usage'].get('cost')}]")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest", nargs="?", type=Path)
    ap.add_argument("--model", default=os.environ.get("CHAT_MODEL", DEFAULT_MODEL))
    ap.add_argument("--out", type=Path, help="default: critique.json beside the manifest")
    ap.add_argument("--compare", nargs=2, type=Path, metavar=("A.json", "B.json"))
    args = ap.parse_args()

    if args.compare:
        a, b = (json.loads(p.read_text()) for p in args.compare)
        diffs = disagreements(a, b)
        for d in diffs:
            print(d["name"])
            for x in d["diffs"]:
                print(f"  {x['requirement']}: {x['a']!r} vs {x['b']!r}")
        print(f"{len(diffs)} image(s) where the two critics disagree. Look at those yourself.")
        return
    if args.manifest is None:
        ap.error("manifest.json is required (or use --compare)")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; the critique is a billed vision call per image. Nothing checked.")
    from openrouter import OpenRouter  # imported here so the no-key path and the tests never need it

    out = args.out or args.manifest.parent / "critique.json"
    results = critique_set(OpenRouter(api_key=key), args.model, args.manifest, out)
    passed = sum(r["passes"] for r in results)
    costs = [u.get("cost") for r in results for u in (r.get("usage", {}), r.get("usage_text", {}))]
    total = sum(c for c in costs if c is not None)
    print(f"{passed}/{len(results)} images pass the code's check, ${total:.4f} total; written to {out}")


if __name__ == "__main__":
    main()
