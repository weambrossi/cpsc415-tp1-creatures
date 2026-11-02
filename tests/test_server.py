"""No-key tests for the web server: spec.md behaviors W1-W9. The two billed calls are fakes."""
import base64
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import server
from app.generator import build_prompt
from tests.fakes import PIXEL_PNG, FakeCritic, FakeImageModel

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fakes():
    image, critic = FakeImageModel(), FakeCritic()
    return image, critic, server.create_app(image, critic).test_client()


def generate(client, **body):
    body = {"description": "a small forest fox kit holding an acorn", "name": "FERNKIT", **body}
    return client.post("/api/generate", json=body)


def test_w1_the_page_is_served_and_holds_no_key(fakes):
    r = fakes[2].get("/")
    assert r.status_code == 200
    assert b"<form" in r.data
    assert b"sk-or" not in r.data


def test_w2_generate_calls_the_image_model_once_with_the_generators_prompt(fakes):
    image, _, client = fakes
    r = generate(client, seed=6301)
    assert r.status_code == 200
    expected = build_prompt("a small forest fox kit holding an acorn", "FERNKIT", seed=6301)
    assert image.calls == [{"prompt": expected["prompt"], "seed": 6301}]
    body = r.get_json()
    assert body["image"] == "data:image/png;base64," + base64.b64encode(PIXEL_PNG).decode()
    assert body["requirements"] == expected["requirements"]
    assert body["expected_text"] == "FERNKIT"
    for field in ("id", "media_type", "seed", "model", "cost", "prompt"):
        assert field in body


def test_w2_seed_defaults_to_6300(fakes):
    image, _, client = fakes
    assert generate(client).status_code == 200
    assert image.calls[0]["seed"] == server.DEFAULT_SEED == 6300


@pytest.mark.parametrize("body", [{"name": ""}, {"description": "  "}, {"description": "x" * 301},
                                  {"seed": "abc"}])
def test_w3_missing_or_oversized_input_is_a_400_and_no_call(fakes, body):
    image, _, client = fakes
    r = generate(client, **body)
    assert r.status_code == 400
    assert "error" in r.get_json()
    assert image.calls == []


@pytest.mark.parametrize("body,message", [({"name": "FERN KIT"}, "1 to 12 letters"),
                                          ({"description": "a pikachu fox"}, "original creature")])
def test_w4_the_generators_refusal_is_shown_and_nothing_is_billed(fakes, body, message):
    image, _, client = fakes
    r = generate(client, **body)
    assert r.status_code == 400
    assert message in r.get_json()["error"]
    assert image.calls == []


def test_w5_critique_uses_the_image_and_entry_the_server_saved(fakes):
    _, critic, client = fakes
    made = generate(client).get_json()
    r = client.post("/api/critique", json={"id": made["id"], "requirements": ["invented by the browser"]})
    assert r.status_code == 200
    assert len(critic.calls) == 1
    call = critic.calls[0]
    assert call["image_bytes"] == PIXEL_PNG
    assert call["entry"]["requirements"] == made["requirements"]      # not the browser's list
    assert call["entry"]["expected_text"] == "FERNKIT"
    body = r.get_json()
    assert body["passes"] is False
    assert body["problems"] == [f"unmet: {made['requirements'][-1]}"]
    assert body["check"]["unmet"] == [made["requirements"][-1]]
    assert [c["requirement"] for c in body["checks"]] == made["requirements"]
    assert body["text_read"] == "FERNKIT" and body["text_matches"] is True
    assert body["expected_text"] == "FERNKIT"
    assert body["cost"] == pytest.approx(0.0015)


def test_w5_a_misread_name_is_a_named_problem():
    client = server.create_app(FakeImageModel(), FakeCritic(unmet_last=False, text_read="FERNK1T")).test_client()
    body = client.post("/api/critique", json={"id": generate(client).get_json()["id"]}).get_json()
    assert body["passes"] is False
    assert body["problems"] == ["name reads 'FERNK1T', expected 'FERNKIT'"]
    assert body["text_matches"] is False


def test_w6_unknown_id_is_a_404_and_no_call(fakes):
    _, critic, client = fakes
    assert client.post("/api/critique", json={"id": "nope"}).status_code == 404
    assert client.post("/api/critique", json={}).status_code == 404
    assert critic.calls == []


def test_w7_critique_before_the_critic_is_merged_is_a_clear_503(monkeypatch):
    monkeypatch.setattr(server.importlib.util, "find_spec", lambda name: None)
    _, real_critique = server.real_functions(client=None)
    client = server.create_app(FakeImageModel(), real_critique).test_client()
    made = generate(client).get_json()
    r = client.post("/api/critique", json={"id": made["id"]})
    assert r.status_code == 503
    assert "not merged yet" in r.get_json()["error"]


def test_w5_the_real_wiring_calls_critique_one_with_the_saved_image_and_entry(monkeypatch):
    calls = []
    fake_module = SimpleNamespace(DEFAULT_MODEL="minimax/minimax-m3",
                                  critique_one=lambda *args: calls.append(args) or FakeCritic()(args[2], {
                                      "requirements": args[5], "expected_text": args[6]}))
    monkeypatch.setattr(server, "load_critic", lambda: fake_module)
    _, real_critique = server.real_functions(client="the-client")
    client = server.create_app(FakeImageModel(), real_critique).test_client()
    made = generate(client).get_json()
    assert client.post("/api/critique", json={"id": made["id"]}).status_code == 200
    assert calls == [("the-client", "minimax/minimax-m3", PIXEL_PNG, "image/png", made["prompt"],
                      made["requirements"], "FERNKIT")]


@pytest.mark.parametrize("route", ["generate", "critique"])
def test_w8_a_failed_model_call_is_a_502_with_the_key_masked(route):
    boom = RuntimeError("401 from provider for key sk-or-v1-0123456789abcdef")
    image = FakeImageModel(error=boom if route == "generate" else None)
    critic = FakeCritic(error=boom if route == "critique" else None)
    client = server.create_app(image, critic).test_client()
    r = generate(client)
    if route == "critique":
        r = client.post("/api/critique", json={"id": r.get_json()["id"]})
    assert r.status_code == 502
    assert "401 from provider" in r.get_json()["error"]
    assert "sk-or" not in r.get_data(as_text=True)
    assert len(image.calls) == 1


def test_w9_no_key_the_server_does_not_start():
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    r = subprocess.run([sys.executable, "-m", "app.server"], cwd=ROOT, env=env,
                       capture_output=True, text=True, check=False, timeout=30)
    assert r.returncode == 1
    assert "OPENROUTER_API_KEY is not set" in r.stderr
