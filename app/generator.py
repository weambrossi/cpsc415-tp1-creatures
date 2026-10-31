"""Generator: a description and a name become one creature image, with a manifest (spec.md, G1-G8).

    python -m app.generator prompts/ethan.json --out images/ethan            # needs OPENROUTER_API_KEY
    python -m app.generator prompts/ethan.json --out /tmp/seed --only profowl

The critic-checker reads the manifest to know what each image was asked to show; the web server
calls build_prompt and generate_one for a single creature.
"""
import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "black-forest-labs/flux.2-klein-4b"
EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

STYLE = ("An original cute creature-collector monster in colorful anime game art style: {description}. "
         "Exactly one creature, centered, full body, on a plain white background. "
         "A banner across the top shows the name \"{name}\" in large, clear capital letters. "
         "No other text anywhere in the image.")

SHARED_REQUIREMENTS = [
    "There is exactly one creature in the image",
    "The background is plain white",
    "The name is shown in a banner at the top",
    "There is no text other than the name",
]

# Original creatures only (CLAUDE.md, TP1 rules): a description naming an existing franchise is refused.
BLOCKED = ("pokemon", "pokémon", "pikachu", "digimon", "nintendo")


def build_prompt(description: str, name: str, seed: int | None = None) -> dict:
    """The full prompt in the team style, the shared requirements, and the name expected in the banner."""
    name = name.strip()
    if not re.fullmatch(r"[A-Za-z]{1,12}", name):
        raise ValueError("name must be 1 to 12 letters, no spaces or digits")
    lowered = description.lower()
    if any(word in lowered for word in BLOCKED):
        raise ValueError("describe an original creature; existing franchises and characters are not allowed")
    text = name.upper()
    return {"name": name.lower(), "prompt": STYLE.format(description=description.strip(), name=text),
            "seed": seed, "requirements": list(SHARED_REQUIREMENTS), "expected_text": text}


def generate_one(client, model: str, prompt: str, seed: int | None, aspect_ratio: str = "1:1") -> dict:
    """One Image API call (POST /api/v1/images through the SDK): image bytes, media type, cost."""
    kwargs = {"seed": seed} if seed is not None else {}
    r = client.images.generate(model=model, prompt=prompt, aspect_ratio=aspect_ratio, **kwargs)
    if not getattr(r, "data", None):
        raise RuntimeError(f"{model} returned no image for this prompt")
    item = r.data[0]
    return {"bytes": base64.b64decode(item.b64_json), "media_type": item.media_type,
            "cost": getattr(r.usage, "cost", None) if r.usage is not None else None}


def run(client, prompts: list[dict], out: Path, model: str, aspect_ratio: str = "1:1",
        only: str | None = None) -> list[dict]:
    """Generate each prompt once (or only the named one), save the images, write manifest.json."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for p in prompts:
        if only and p["name"] != only:
            continue
        t0 = time.time()
        g = generate_one(client, model, p["prompt"], p["seed"], aspect_ratio)
        path = out / f"{p['name']}.{EXT.get(g['media_type'], 'bin')}"
        path.write_bytes(g["bytes"])
        entry = {**p, "model": model, "aspect_ratio": aspect_ratio, "file": path.name,
                 "media_type": g["media_type"], "cost": g["cost"], "seconds": round(time.time() - t0, 1)}
        manifest.append(entry)
        # Written after every image, so a failure later in the run keeps the record of what was paid for.
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"{path}  {g['media_type']}  seed={p['seed']}  ${g['cost']}  {entry['seconds']}s")
    if not manifest:
        (out / "manifest.json").write_text("[]\n")
    return manifest


def summary(manifest: list[dict]) -> str:
    """One line: image count and total cost, saying how many replies carried no cost."""
    missing = sum(1 for e in manifest if e["cost"] is None)
    line = f"{len(manifest)} image(s), ${sum(e['cost'] for e in manifest if e['cost'] is not None):.4f} total"
    return line + (f", cost missing for {missing} image(s)" if missing else "")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("prompts", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", default=os.environ.get("IMAGE_MODEL", DEFAULT_MODEL),
                    help="image model slug (default: $IMAGE_MODEL, else FLUX.2 klein)")
    ap.add_argument("--aspect-ratio", default="1:1")
    ap.add_argument("--only", help="generate just the prompt with this name")
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; image generation is a billed call. Nothing generated.")
    from openrouter import OpenRouter  # imported here so the no-key path and the tests never need it

    manifest = run(OpenRouter(api_key=key), json.loads(args.prompts.read_text()), args.out,
                   args.model, args.aspect_ratio, args.only)
    print(summary(manifest))


if __name__ == "__main__":
    main()
