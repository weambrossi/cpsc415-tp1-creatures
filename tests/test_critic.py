"""No-key tests for the critic-checker: spec.md behaviors C1-C11. The chat endpoint is a fake client."""
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.critic import check, critique_one, critique_set, disagreements, extract_json, text_matches

ROOT = Path(__file__).resolve().parents[1]
REQS = ["There is exactly one creature in the image", "The background is plain white",
        "The name is shown in a banner at the top"]


def critique_with(*met):
    return {"checks": [{"requirement": r, "met": m, "evidence": "x"} for r, m in zip(REQS, met)]}


class FakeChat:
    """Answers the checklist question with `checklist` and the name question with `name`."""

    def __init__(self, checklist, name="EMBERPUP", cost=0.001, fail=None):
        self.checklist, self.name, self.cost, self.fail = checklist, name, cost, fail
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail and len(self.calls) in self.fail:
            raise RuntimeError("upstream 502")
        question = kwargs["messages"][0]["content"][0]["text"]
        content = self.checklist if "Items:" in question else self.name
        usage = SimpleNamespace(prompt_tokens=1500, completion_tokens=300, cost=self.cost)
        return SimpleNamespace(usage=usage, choices=[SimpleNamespace(
            finish_reason="stop", message=SimpleNamespace(content=content))])


def client(chat):
    return SimpleNamespace(chat=chat)


# ---------- check: C1-C6 ----------

def test_all_met_is_ok():
    assert check(REQS, critique_with(True, True, True)) == {
        "ok": True, "problems": [], "unmet": [], "missing": [], "extra": []}


def test_c5_one_unmet_requirement_is_named():
    result = check(REQS, critique_with(True, False, True))
    assert not result["ok"]
    assert result["unmet"] == ["The background is plain white"]
    assert any("The background is plain white" in p for p in result["problems"])


def test_c3_unanswered_requirement_is_a_problem_even_if_the_rest_pass():
    result = check(REQS, critique_with(True, True))
    assert not result["ok"]
    assert result["missing"] == [REQS[2]]
    assert any(REQS[2] in p for p in result["problems"])


def test_c4_invented_requirement_is_a_problem():
    c = critique_with(True, True, True)
    c["checks"].append({"requirement": "The lighting is dramatic", "met": True})
    result = check(REQS, c)
    assert not result["ok"]
    assert result["extra"] == ["The lighting is dramatic"]
    assert any("The lighting is dramatic" in p for p in result["problems"])


@pytest.mark.parametrize("met", ["yes", "true", 1, None])
def test_c5_met_that_is_not_a_boolean_counts_as_unanswered(met):
    c = critique_with(True, True, True)
    c["checks"][1]["met"] = met
    result = check(REQS, c)
    assert not result["ok"]
    assert result["missing"] == [REQS[1]]
    assert result["unmet"] == []


def test_c5_same_requirement_answered_twice_with_different_verdicts_counts_as_unanswered():
    c = critique_with(True, True, True)
    c["checks"].append({"requirement": REQS[0], "met": False})
    result = check(REQS, c)
    assert not result["ok"]
    assert result["missing"] == [REQS[0]]


def test_c6_requirement_text_is_matched_ignoring_case_and_punctuation():
    c = {"checks": [{"requirement": "there is exactly one creature in the image.", "met": True},
                    {"requirement": "The background is  PLAIN white", "met": True},
                    {"requirement": REQS[2], "met": True}]}
    assert check(REQS, c)["ok"]


@pytest.mark.parametrize("reply", ["Sorry, I can't see any image.", "", None, '{"checks": [{"requirement": "Th',
                                   '{"verdict": "looks good"}', "[1, 2, 3]"])
def test_c1_not_json_is_a_failed_critique_not_a_crash(reply):
    result = check(REQS, extract_json(reply))
    assert not result["ok"]
    assert result["missing"] == REQS
    assert result["problems"]


def test_c2_json_inside_prose_and_fences_is_extracted():
    text = 'Here is my check:\n```json\n{"checks": [{"requirement": "a", "met": true}]}\n```\nDone.'
    assert extract_json(text) == {"checks": [{"requirement": "a", "met": True}]}


# ---------- the name: C7 ----------

def test_c7_name_match_ignores_case_and_surrounding_punctuation():
    assert text_matches("EMBERPUP", "  emberpup! ")
    assert text_matches("EMBERPUP", '"EMBERPUP"')


@pytest.mark.parametrize("read", ["EMBERPUF", "EMBER PUP", "EMBERPUPP", "", None])
def test_c7_name_mismatch(read):
    assert not text_matches("EMBERPUP", read)


# ---------- critique_one: C7, C8 ----------

def test_c8_two_calls_and_a_pass_when_everything_matches():
    chat = FakeChat(json.dumps(critique_with(True, True, True)), name="EMBERPUP")
    r = critique_one(client(chat), "minimax/minimax-m3", b"img", "image/jpeg", "a fire pup", REQS, "EMBERPUP")
    assert len(chat.calls) == 2
    assert all(c["model"] == "minimax/minimax-m3" for c in chat.calls)
    image = chat.calls[0]["messages"][0]["content"][1]["image_url"]["url"]
    assert image.startswith("data:image/jpeg;base64,")
    assert r["passes"] is True
    assert r["problems"] == []
    assert r["text_read"] == "EMBERPUP"
    assert r["usage"]["cost"] == 0.001
    assert r["usage"]["finish"] == "stop"


def test_c7_misspelled_name_fails_even_when_the_checklist_says_the_banner_is_fine():
    chat = FakeChat(json.dumps(critique_with(True, True, True)), name="EMBERPUF")
    r = critique_one(client(chat), "m", b"img", "image/jpeg", "p", REQS, "EMBERPUP")
    assert r["check"]["ok"] is True
    assert r["text_matches"] is False
    assert r["passes"] is False
    assert any("EMBERPUF" in p and "EMBERPUP" in p for p in r["problems"])


def test_c8_one_call_without_expected_text():
    chat = FakeChat(json.dumps(critique_with(True, True, True)))
    r = critique_one(client(chat), "m", b"img", "image/png", "p", REQS)
    assert len(chat.calls) == 1
    assert r["passes"] is True
    assert "text_read" not in r


def test_c8_missing_cost_is_null_not_zero():
    chat = FakeChat(json.dumps(critique_with(True, True, True)), cost=None)
    r = critique_one(client(chat), "m", b"img", "image/jpeg", "p", REQS, "EMBERPUP")
    assert r["usage"]["cost"] is None


def test_c1_refusal_through_critique_one_is_a_failed_critique():
    chat = FakeChat(None, name="EMBERPUP")
    r = critique_one(client(chat), "m", b"img", "image/jpeg", "p", REQS, "EMBERPUP")
    assert r["critique"] is None
    assert r["passes"] is False


def test_mimo_runs_with_reasoning_off():
    chat = FakeChat(json.dumps(critique_with(True, True, True)))
    critique_one(client(chat), "xiaomi/mimo-v2.6-flash", b"img", "image/jpeg", "p", REQS)
    assert chat.calls[0]["reasoning"] == {"effort": "none"}


# ---------- critique_set: C9 ----------

def write_manifest(tmp_path, names):
    entries = []
    for n in names:
        (tmp_path / f"{n}.jpg").write_bytes(b"img")
        entries.append({"name": n, "prompt": f"a {n}", "requirements": REQS, "expected_text": "EMBERPUP",
                        "file": f"{n}.jpg", "media_type": "image/jpeg"})
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(entries))
    return path


def test_c9_one_critique_per_image_and_the_file_is_written(tmp_path):
    chat = FakeChat(json.dumps(critique_with(True, True, True)))
    out = tmp_path / "critique.json"
    results = critique_set(client(chat), "m", write_manifest(tmp_path, ["a", "b"]), out)
    assert [r["name"] for r in results] == ["a", "b"]
    assert len(chat.calls) == 4
    assert json.loads(out.read_text()) == results


def test_c9_an_api_error_on_one_image_is_recorded_and_the_run_goes_on(tmp_path):
    chat = FakeChat(json.dumps(critique_with(True, True, True)), fail={1})
    out = tmp_path / "critique.json"
    results = critique_set(client(chat), "m", write_manifest(tmp_path, ["a", "b"]), out)
    assert results[0]["passes"] is False
    assert "upstream 502" in results[0]["error"]
    assert results[1]["passes"] is True
    assert len(json.loads(out.read_text())) == 2


# ---------- disagreements: C10 ----------

def test_c10_two_critics_disagreeing():
    a = [{"name": "p1", "critique": critique_with(True, True, True), "text_read": "EMBERPUP"}]
    b = [{"name": "p1", "critique": critique_with(True, False, True), "text_read": "EMBERPUF"}]
    d = disagreements(a, b)
    assert len(d) == 1
    assert {x["requirement"] for x in d[0]["diffs"]} == {REQS[1], "<text read>"}
    assert disagreements(a, a) == []


def test_c10_image_in_only_one_file_is_named():
    a = [{"name": "p1", "critique": critique_with(True, True, True)},
         {"name": "p2", "critique": critique_with(True, True, True)}]
    d = disagreements(a, a[:1])
    assert [x["name"] for x in d] == ["p2"]


def test_c10_compares_ethans_two_critique_files_without_a_key():
    a = json.loads((ROOT / "images/ethan/critique.json").read_text())
    b = json.loads((ROOT / "images/ethan/critique-mimo.json").read_text())
    assert disagreements(a, b) == []          # images/ethan/README.md: the two critics did not disagree


# ---------- CLI: C11 ----------

def no_key_env():
    return {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}


def test_c11_no_key_no_call():
    r = subprocess.run([sys.executable, "-m", "app.critic", "images/ethan/manifest.json", "--out", "/tmp/x.json"],
                       cwd=ROOT, env=no_key_env(), capture_output=True, text=True, check=False)
    assert r.returncode == 1
    assert "OPENROUTER_API_KEY is not set" in r.stderr


def test_c11_compare_needs_no_key():
    r = subprocess.run([sys.executable, "-m", "app.critic", "--compare", "images/ethan/critique.json",
                        "images/ethan/critique-mimo.json"],
                       cwd=ROOT, env=no_key_env(), capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert "0 image(s) where the two critics disagree" in r.stdout
