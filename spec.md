# Spec

<!-- The agent writes this from the approved intent. You validate it against the intent.
     If the spec and the intent disagree, the intent wins until you change the intent. -->

## Intent
One intent per major feature, each approved by its owner:
- [`intent/generator.md`](intent/generator.md) (Ethan): text to creature image, with a manifest.
- [`intent/critic.md`](intent/critic.md) (Joud): the vision critique, checked in code.
- `intent/web-app.md` (Lane): the page and the server that holds the key. _Plan task L2._

## Components
One section per component, each written by its owner. Two design decisions are required for
each: language and model, with the alternative considered. Behaviors are numbered per component
(G, C, W) so three people can add theirs without renumbering each other's.

### Generator (`app/generator.py`), owner Ethan
- **What it does:** turns a description and a name into a full prompt in the team style
  (`build_prompt`), makes one Image API call per prompt (`generate_one`), saves the image, and
  writes `manifest.json` with what was asked for and what it cost (`run`).
- **Language:** Python 3.13. **Why:** the `openrouter` SDK and the course examples are Python, and
  the critic and the server import the generator directly. Java was considered; it has no
  OpenRouter SDK, so the Image API request would be written by hand for no gain.
- **Model:** `black-forest-labs/flux.2-klein-4b`. **Why:** compared with
  `google/gemini-3.1-flash-lite-image` on the same prompt and seed (PROFOWL, seed 6101, Ethan's
  Week 6 lab): FLUX cost $0.014 and followed every requirement, including "no text other than the
  name"; Gemini cost $0.0336 (2.4x) and printed "ARCANE KNOWLEDGE" on the book, breaking that
  requirement. Both spelled the name correctly. FLUX with the same seed gave the same picture with
  different file bytes.
- **Interfaces:**
  - `build_prompt(description, name, seed=None) -> dict` with `name` (lowercase slug), `prompt`,
    `seed`, `requirements` (the four shared ones), `expected_text` (the name in capitals).
  - `generate_one(client, model, prompt, seed, aspect_ratio="1:1") -> {"bytes", "media_type", "cost"}`.
  - `run(client, prompts, out_dir, model, aspect_ratio="1:1", only=None) -> manifest`; writes the
    images and `out_dir/manifest.json`.
  - CLI: `python -m app.generator PROMPTS.json --out DIR [--model SLUG] [--only NAME]`
    `--model` defaults to the `IMAGE_MODEL` environment variable, else `black-forest-labs/flux.2-klein-4b`; the
    server uses the same default.
  - Manifest entry: `name`, `prompt`, `seed`, `requirements`, `expected_text`, `model`,
    `aspect_ratio`, `file`, `media_type`, `cost`, `seconds`.
- **Dependencies:** `openrouter`.

**Behavior (no key unless marked)**
- G1. `build_prompt` puts the description and the name, in capitals, into the fixed style text,
  and asks for exactly one creature, a plain white background, the name in a banner at the top,
  and no other text.
- G2. `build_prompt` returns the four shared requirements: exactly one creature; plain white
  background; the name in a banner at the top; no text other than the name.
- G3. A name that is empty, longer than 12 characters, or not letters only is rejected with
  `ValueError` before any call.
- G4. A description that names an existing franchise or character is rejected with `ValueError`;
  the app makes original creatures only. The blocked words are `BLOCKED` in `app/generator.py`:
  pokemon, pokémon, pikachu, digimon, nintendo.
- G5. `run` makes one call per prompt with the prompt, seed, and model as given, and writes one
  manifest entry per prompt with every field above. `requirements` is the prompt's own list: the
  four shared ones from `build_prompt`, plus any per-creature requirements a prompts file adds
  (Ethan's adds two per creature). `cost` is the reply's `usage.cost`, or `null` when the reply has
  none; the summary line says how many costs were missing instead of counting them as $0.
- G6. `run(..., only=NAME)` makes exactly one call.
- G7. Without `OPENROUTER_API_KEY` the CLI prints one line to stderr saying so and exits 1;
  nothing is billed.
- G8 (key, by hand). Ethan's five-prompt set in `prompts/ethan.json`, generated once, is in
  `images/ethan/` with its manifest and both critique files.

**Failure handling.** A model that rejects `seed` or `aspect_ratio`, or a network failure, raises;
the error is shown and nothing is retried. A reply with no image raises `RuntimeError` naming the
model. `manifest.json` is rewritten after every image, so a failure partway through keeps the
entries for the images already generated and paid for. A misspelled name in the image is the critic-checker's to report; the
generator never regenerates. No key: G7.

**Cost.** One FLUX image is about $0.014. A demo of five creatures is $0.07; a semester of one
creature a day is about $1.50.

### Critic-checker (`app/critic.py`), owner Joud
- **What it does:** sends each image with its requirements to a vision model as a yes/no checklist
  (`critique_one`), asks a second narrow question for the name in the banner, and checks both
  answers in plain code (`check`, `text_matches`). `critique_set` runs a whole manifest and
  `disagreements` compares two critique files.
- **Language:** Python 3.13. **Why:** it reads the generator's manifest and is imported by the
  server, both Python, and the `openrouter` SDK sends the image as a data URL on the chat endpoint.
  JavaScript in the browser was considered and ruled out: the key would have to reach the page.
- **Model:** `minimax/minimax-m3`, checked by `xiaomi/mimo-v2.6-flash`. **Why:** on Ethan's five
  images minimax cost about $0.001 per checklist plus $0.0005 for the name, so a full critique is
  under a cent per image. A second, different model is the only check on the critic that does not
  need a person; where the two disagree, a person looks. MiMo runs with reasoning off
  (`effort: none`) so hidden reasoning does not eat the token budget. A frontier model was
  considered and ruled out on cost: the checklist is yes/no questions about a simple image.
- **Interfaces:**
  - `extract_json(text) -> dict | None`: the JSON object inside a reply, fenced or in prose.
  - `check(requirements, critique) -> {"ok", "problems", "unmet", "missing", "extra"}`.
  - `text_matches(expected, read) -> bool`.
  - `critique_one(client, model, image_bytes, media_type, prompt, requirements, expected_text=None)
    -> result` with `model`, `critique`, `raw`, `usage`, `check`, `text_read`, `text_matches`,
    `usage_text`, `passes`, `problems`. The server calls this for one image.
  - `critique_set(client, model, manifest_path, out_path) -> [result + "name"]`.
  - `disagreements(a, b) -> [{"name", "diffs"}]`.
  - CLI: `python -m app.critic MANIFEST [--model SLUG] [--out FILE]` and
    `python -m app.critic --compare A.json B.json`. `--model` defaults to `CHAT_MODEL`, else
    `minimax/minimax-m3`; `--out` defaults to `critique.json` beside the manifest.
- **Dependencies:** `openrouter` (already listed).

**Behavior (no key unless marked)**
- C1. A reply that is not the JSON checklist (prose, a refusal, an empty reply, a reply cut off at
  the token limit) is a failed critique: `ok` is false and every requirement is listed as missing.
  Nothing raises.
- C2. JSON inside prose or a code fence is extracted and checked.
- C3. A requirement the critic did not answer is a problem, named in `problems`.
- C4. An item the critic answered that was not asked (an invented requirement) is a problem, named.
- C5. A requirement is met only when `met` is the JSON value `true`. `false` makes it unmet; a
  `met` that is not a boolean (`"yes"`, `1`, missing) counts as unanswered; the same requirement
  answered twice with different verdicts counts as unanswered. Each is named.
- C6. Requirement text is matched ignoring case, spacing, and punctuation.
- C7. The name is read by a second call ("write the largest text exactly as printed") and compared
  in code with `expected_text`, ignoring case and surrounding punctuation. A mismatch or an empty
  read is a problem naming both strings. The checklist's own answer about the banner does not
  override this.
- C8. `critique_one` makes exactly two calls with an `expected_text`, one without. `passes` is true
  only when `check` is ok and the name matches. `usage` records tokens, finish reason, and the
  reply's `cost`, or `null` when the reply has none.
- C9. `critique_set` makes one `critique_one` per manifest entry and rewrites the output file after
  each image. An API error on one image is recorded on that entry as a failed critique with the
  error text, and the run goes on to the next image.
- C10. `disagreements` lists, per image, every requirement and the name read where the two files
  differ, and names images that are in only one file.
- C11. Without `OPENROUTER_API_KEY` the CLI prints one line to stderr saying so and exits 1;
  nothing is billed. `--compare` needs no key.
- C12 (key, by hand). Joud's five-prompt set (`prompts/joud.json`, one creature per element:
  fire, water, leaf, stone, storm) is generated once and critiqued once by each model, in
  `images/joud/` with `manifest.json`, `critique.json`, and `critique-mimo.json`.

**Failure handling.** Bad JSON is C1. A network or API error on a single-image call raises to the
caller (the server shows it); in `critique_set` it is C9. Nothing is retried. A model that
disagrees with itself (checklist says the banner is fine, the name read does not match) fails the
image: the code trusts the narrow question over the broad one.

**Cost.** About $0.0015 per image per critic. Both critics on five images is under $0.02.

### Web app (`app/server.py`, `static/`), owner Lane
- **What it does:** serves the page, and on two routes calls the generator and the critic for the
  browser, adding the key on the server. The browser sends a description, a name, and a seed, and
  later an id; it never sends an image, a model name, or requirements.
- **Language:** Python 3 (3.11 in my `.venv`). **Why:** the generator and the critic-checker are Python modules, and
  the server imports them directly. Java (the course's `Server.java`) would have to call them
  through another process or copy them.
- **Framework:** Flask. **Why:** compared with the standard library's `http.server`, as in the
  course's `examples/key-on-server/server.py`: Flask is one decorated function per URL, with
  `request.get_json()` and `jsonify` in place of a hand-written handler class, and
  `app.test_client()` lets the no-key tests call each route without starting a server.
  `http.server` needs no dependency, but every test would need a running server on a port.
- **Model:** none chosen here. The server uses the generator's default image model
  (`IMAGE_MODEL`, else FLUX.2 klein) and the critic's default vision model. The page has no model
  field, so a visitor cannot pick a more expensive one.
- **Interfaces:**
  - `create_app(make_image, critique)` returns the Flask app. The two arguments are the only
    billed calls: `make_image(prompt, seed)` returns `bytes`, `media_type`, `cost`, `model`, and
    `critique(image_bytes, entry)` returns what `app.critic.critique_one` returns (Critic-checker,
    C8). `real_functions(client)` gives the real pair: `app.generator.generate_one`, and
    `app.critic.critique_one(client, model, image_bytes, media_type, prompt, requirements,
    expected_text)` with the critic's own `DEFAULT_MODEL`. Tests pass the fakes in
    `tests/fakes.py`. The prompt always comes from the real `app.generator.build_prompt`, so its
    name and franchise rules apply.
  - `GET /` serves `static/index.html`.
  - `POST /api/generate` with JSON `{"description", "name", "seed"}` returns 200 with `id`,
    `image` (a `data:` URL), `media_type`, `seed`, `model`, `cost`, `seconds`, `prompt`,
    `requirements`, `expected_text`.
  - `POST /api/critique` with JSON `{"id"}` returns 200 with the critic-checker's `passes` and
    `problems`, its `check` (`ok`, `problems`, `unmet`, `missing`, `extra`), the critic's `checks`
    (each `requirement`, `met`, `evidence`), `text_read`, `expected_text`, `text_matches`,
    `model`, and `cost` (the critic-checker's own two calls, checklist and name read, added up; the
    image's cost is the generate reply's `cost`, and the page adds the two for its total; `null`
    when either critic reply had no cost or the result carries no usage at all; never
    counted as $0).
  - Errors are JSON `{"error": "<message>"}`.
  - `python -m app.server [--port 8000]` starts it on localhost.
- **Dependencies:** `flask`, `playwright` (repository-wide table below).

**Behavior (no key unless marked)**
- W1. `GET /` serves the page; the page contains no key.
- W2. `POST /api/generate` calls `make_image` exactly once, with the prompt from `build_prompt`
  and the seed as given (6300 when none is given), and returns the image as a `data:` URL with
  the manifest fields above.
- W3. A missing or empty description or name, or a description over 300 characters, gets a 400
  and no call.
- W4. A name or description the generator refuses (its `ValueError`) gets a 400 with the
  generator's own message, and no image call.
- W5. `POST /api/critique` with an id from this server calls `critique` exactly once, on the image
  and the manifest entry the server saved, and returns its result; a misread banner name is one
  of the named problems. The browser cannot send its own image or requirements.
- W6. An unknown id gets a 404 and no call.
- W7. While `app/critic.py` does not exist (until PR #3 merges), `POST /api/critique` gets a 503 saying the
  critic-checker is not merged yet.
- W8. A model call that raises, or returns something the server cannot read, gets a JSON 502
  with the error message; any `sk-or-...` text in it is replaced with `[key]`. Nothing is retried.
- W9. Without `OPENROUTER_API_KEY`, `python -m app.server` prints one line saying so and exits 1;
  `create_app` with fakes needs no key.
- W10. The page shows, for each requirement the critic answered, met or not met with its
  evidence; the critic-checker's verdict and every problem it named (unmet, not answered,
  invented, misread name); the banner text read against the expected name, match or mismatch;
  and any error message from the server.
- W11 (browser, `tests/test_browser.py`, no key). Playwright starts the app with fakes, types a
  description and a name, clicks Generate, and waits for the image and the checklist. It asserts
  that the page contains no `sk-or`, that no request the browser made carried an `Authorization`
  header or went to openrouter.ai, and that the browser called `/api/generate` and
  `/api/critique`. It is skipped where Playwright or Chromium is not installed.
- W12 (key, marked `model`, by hand once). The same browser test against the real generator and
  critic: one generation and one critique, about $0.016.

**Failure handling.** See W3–W8. The image and its manifest entry are kept in memory for as long
as the server runs; restarting the server forgets them, and an old id then gets W6.

**Cost.** One click is one FLUX image (about $0.014) and one critique (about $0.002). The tests
call no model except W12.

## Out of scope
Carried over from the intents: regenerating or editing a failed image, choosing the best of
several images, accounts and storage, hosting (the presentation runs on localhost), and audio.

## Dependencies (repository-wide)
| Package | Why | By hand it would be |
|---|---|---|
| `openrouter` | The official OpenRouter SDK: `client.images.generate` for the Image API and `client.chat.send` for the vision critique, one client object for both request shapes. | Two hand-built `urllib.request` calls with manual JSON, base64 and error handling, as in Weeks 2–5. |
| `pytest` | Runs the no-key tests and the release gate (`gate.sh`, `gate.yml`). | A hand-rolled test runner. |
| `ruff` | The linter the release gate runs before every push. | No lint step. |
| `flask` | The web server (Web app): one decorated function per route, JSON in and out, and a test client so the no-key server tests run without a port. | `http.server` with a hand-written handler class, as in the course's key-on-server example, and a running server for every test. |
| `playwright` | Drives a real Chromium for the browser check (W11): types, clicks, and records every request the page made, so the test can show the key never left the server. Needs `playwright install chromium` once. | Nothing: without a real browser there is no way to see which requests the page itself made. |
