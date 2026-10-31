"""No-key tests for the generator: spec.md behaviors G1-G7. The Image API is a fake client."""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.generator import SHARED_REQUIREMENTS, build_prompt, run

ROOT = Path(__file__).resolve().parents[1]


class FakeImages:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        item = SimpleNamespace(b64_json=base64.b64encode(b"fake-jpeg").decode(), media_type="image/jpeg")
        return SimpleNamespace(data=[item], usage=SimpleNamespace(cost=0.014))


def fake_client():
    return SimpleNamespace(images=FakeImages())


def test_g1_prompt_carries_description_name_and_style():
    p = build_prompt("a professor owl wearing round glasses", "Profowl", seed=6101)
    assert "a professor owl wearing round glasses" in p["prompt"]
    assert '"PROFOWL"' in p["prompt"]
    for phrase in ("Exactly one creature", "plain white background", "banner", "No other text"):
        assert phrase in p["prompt"]
    assert p["name"] == "profowl"
    assert p["expected_text"] == "PROFOWL"
    assert p["seed"] == 6101


def test_g2_shared_requirements():
    assert build_prompt("a robot", "BOLTBIT")["requirements"] == SHARED_REQUIREMENTS
    assert len(SHARED_REQUIREMENTS) == 4


@pytest.mark.parametrize("name", ["", "PROF OWL", "PROFOWL2", "SUPERCALIFRAGI"])
def test_g3_bad_name_is_rejected(name):
    with pytest.raises(ValueError):
        build_prompt("an owl", name)


@pytest.mark.parametrize("description", ["a Pokemon owl", "pikachu but blue", "a DIGIMON fox"])
def test_g4_franchise_names_are_rejected(description):
    with pytest.raises(ValueError):
        build_prompt(description, "OWLY")


def test_g5_one_call_per_prompt_and_a_full_manifest(tmp_path):
    prompts = [build_prompt("an owl", "PROFOWL", seed=1), build_prompt("a fox", "STUDEX", seed=2)]
    client = fake_client()
    manifest = run(client, prompts, tmp_path, "black-forest-labs/flux.2-klein-4b")
    assert [(c["prompt"], c["seed"]) for c in client.images.calls] == [(p["prompt"], p["seed"]) for p in prompts]
    for entry in manifest:
        for field in ("name", "prompt", "seed", "requirements", "expected_text", "model", "aspect_ratio",
                      "file", "media_type", "cost", "seconds"):
            assert field in entry
        assert entry["cost"] == 0.014
        assert (tmp_path / entry["file"]).read_bytes() == b"fake-jpeg"
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest


def test_g6_only_makes_one_call(tmp_path):
    prompts = [build_prompt("an owl", "PROFOWL", seed=1), build_prompt("a fox", "STUDEX", seed=2)]
    client = fake_client()
    assert [e["name"] for e in run(client, prompts, tmp_path, "m", only="studex")] == ["studex"]
    assert len(client.images.calls) == 1


def test_g7_no_key_no_call():
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    r = subprocess.run([sys.executable, "-m", "app.generator", "prompts/ethan.json", "--out", "/tmp/x"],
                       cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    assert r.returncode == 1
    assert "OPENROUTER_API_KEY is not set" in r.stderr


def test_g5_missing_cost_is_reported_not_counted_as_zero(tmp_path):
    class NoCost(FakeImages):
        def generate(self, **kwargs):
            r = super().generate(**kwargs)
            r.usage = None
            return r

    from app.generator import summary
    client = SimpleNamespace(images=NoCost())
    manifest = run(client, [build_prompt("an owl", "PROFOWL", seed=1)], tmp_path, "m")
    assert manifest[0]["cost"] is None
    assert summary(manifest) == "1 image(s), $0.0000 total, cost missing for 1 image(s)"
    manifest[0]["cost"] = 0.014
    assert summary(manifest) == "1 image(s), $0.0140 total"
