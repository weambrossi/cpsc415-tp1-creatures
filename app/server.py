"""Web app: serves the page, and calls the generator and the critic for the browser with the key on
the server (spec.md, Web app, W1-W12).

    export OPENROUTER_API_KEY=...        # the server reads it; the browser never sees it
    python -m app.server                 # then open http://localhost:8000

The browser sends a description, a name, and a seed, and later the id it got back. It never sends
an image, a model name, or requirements: the server critiques only images it made itself, against
the requirements the generator wrote for them. Images are kept in memory while the server runs.
"""
import argparse
import base64
import importlib
import importlib.util
import os
import re
import sys
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from app.generator import DEFAULT_MODEL as DEFAULT_IMAGE_MODEL
from app.generator import EXT, build_prompt, generate_one

STATIC = Path(__file__).resolve().parent.parent / "static"
DEFAULT_SEED = 6300
MAX_DESCRIPTION = 300
KEY_TEXT = re.compile(r"sk-or-[A-Za-z0-9_-]*")


class CriticMissing(Exception):
    """Joud's critic-checker (plan PR 2) is not in the repository yet."""


def create_app(make_image, critique) -> Flask:
    """The app. make_image(prompt, seed) and critique(image_bytes, entry) are the two billed calls;
    real_functions() gives the real ones, tests/fakes.py the fakes."""
    app = Flask(__name__, static_folder=None)
    made = {}   # id -> (image bytes, manifest entry); kept while the server runs

    @app.get("/")
    def page():
        return send_from_directory(STATIC, "index.html")

    @app.post("/api/generate")
    def generate():
        data = request.get_json(silent=True) or {}
        description = str(data.get("description") or "").strip()
        name = str(data.get("name") or "").strip()
        if not description or not name:
            return error(400, "Type a description and a name.")
        if len(description) > MAX_DESCRIPTION:
            return error(400, f"Keep the description under {MAX_DESCRIPTION} characters.")
        try:
            seed = DEFAULT_SEED if data.get("seed") in (None, "") else int(data["seed"])
        except (TypeError, ValueError):
            return error(400, "The seed must be a whole number.")
        try:
            p = build_prompt(description, name, seed)   # the generator's own name and franchise rules
        except ValueError as e:
            return error(400, str(e))
        try:
            t0 = time.time()
            g = make_image(p["prompt"], seed)
            entry = {**p, "model": g["model"], "aspect_ratio": "1:1",
                     "file": f"{p['name']}.{EXT.get(g['media_type'], 'bin')}",
                     "media_type": g["media_type"], "cost": g["cost"], "seconds": round(time.time() - t0, 1)}
            data_url = f"data:{g['media_type']};base64,{base64.b64encode(g['bytes']).decode()}"
        except Exception as e:  # noqa: BLE001  any failure in the call or its reply is shown, never retried
            return error(502, f"The image call failed: {e!r}")
        image_id = uuid.uuid4().hex
        made[image_id] = (g["bytes"], entry)
        return jsonify({"id": image_id, "image": data_url, **{k: v for k, v in entry.items() if k != "file"}})

    @app.post("/api/critique")
    def critique_route():
        image_id = (request.get_json(silent=True) or {}).get("id")
        if image_id not in made:
            return error(404, "Unknown image. Generate it again (the server forgets images when it restarts).")
        image_bytes, entry = made[image_id]
        try:
            result = critique(image_bytes, entry)
            body = critique_reply(result, entry)
        except CriticMissing as e:
            return error(503, str(e))
        except Exception as e:  # noqa: BLE001  any failure in the call or its reply is shown, never retried
            return error(502, f"The critique call failed: {e!r}")
        return jsonify(body)

    return app


def critique_reply(result: dict, entry: dict) -> dict:
    """What the page needs from the critic-checker's result. Raises if the result is not the shape
    app.critic.critique_one returns, so the route answers with a JSON 502 instead of a crash."""
    if not isinstance(result, dict):
        raise TypeError(f"the critic-checker returned {type(result).__name__}, not a result")
    costs = [(result.get(k) or {}).get("cost") for k in ("usage", "usage_text") if k in result]
    return {
        "passes": result.get("passes") is True,
        "problems": list(result.get("problems") or []),
        "check": result.get("check"),
        "checks": (result.get("critique") or {}).get("checks") or [],
        "text_read": result.get("text_read"),
        "text_matches": result.get("text_matches"),
        "expected_text": entry["expected_text"],
        "model": result.get("model"),
        # Both calls' costs added up; null when either reply carried none, never counted as $0.
        "cost": sum(costs) if costs and all(isinstance(c, (int, float)) for c in costs) else None,
    }


def error(status: int, message: str):
    """A JSON error with anything that looks like a key masked."""
    return jsonify({"error": KEY_TEXT.sub("[key]", message)}), status


def load_critic():
    if importlib.util.find_spec("app.critic") is None:
        raise CriticMissing("The critic-checker (app/critic.py, PR 2) is not merged yet, so there is no critique.")
    return importlib.import_module("app.critic")


def real_functions(client):
    """The two billed calls, through one OpenRouter client that holds the key."""
    image_model = os.environ.get("IMAGE_MODEL", DEFAULT_IMAGE_MODEL)

    def make_image(prompt, seed):
        return {**generate_one(client, image_model, prompt, seed), "model": image_model}

    def critique(image_bytes, entry):
        critic = load_critic()   # the critic's model choice is Joud's: app.critic.DEFAULT_MODEL
        return critic.critique_one(client, critic.DEFAULT_MODEL, image_bytes, entry["media_type"],
                                   entry["prompt"], entry["requirements"], entry["expected_text"])

    return make_image, critique


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; the server adds it to every model call. Not started.")
    # Imported here so the no-key path and the tests never need the SDK.
    from openrouter import OpenRouter

    app = create_app(*real_functions(OpenRouter(api_key=key)))
    print(f"http://localhost:{args.port}")
    app.run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
