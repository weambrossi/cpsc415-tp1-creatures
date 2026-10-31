# Spec

<!-- The agent writes this from the approved intent. You validate it against the intent.
     If the spec and the intent disagree, the intent wins until you change the intent. -->

## Intent
One intent per major feature, each approved by its owner:
- [`intent/generator.md`](intent/generator.md) (Ethan): text to creature image, with a manifest.
- `intent/critic.md` (Joud): the vision critique, checked in code. _Plan task J3._
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
  - CLI: `python -m app.generator PROMPTS.json --out DIR [--model SLUG] [--only NAME]`.
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

**Failure handling.** A model that rejects `seed` or `aspect_ratio` raises; the error is shown,
nothing is retried. A misspelled name in the image is the critic-checker's to report; the
generator never regenerates. No key: G7.

**Cost.** One FLUX image is about $0.014. A demo of five creatures is $0.07; a semester of one
creature a day is about $1.50.

### Critic-checker (`app/critic.py`), owner Joud
_Written by Joud (plan task J3): language and model decisions, numbered behaviors C1..._

### Web app (`app/server.py`, `static/`), owner Lane
_Written by Lane (plan task L2): language and framework decisions, numbered behaviors W1..._

## Out of scope
Carried over from the intents: regenerating or editing a failed image, choosing the best of
several images, accounts and storage, hosting (the presentation runs on localhost), and audio.

## Dependencies (repository-wide)
| Package | Why | By hand it would be |
|---|---|---|
| `openrouter` | The official OpenRouter SDK: `client.images.generate` for the Image API and `client.chat.send` for the vision critique, one client object for both request shapes. | Two hand-built `urllib.request` calls with manual JSON, base64 and error handling, as in Weeks 2–5. |
| `pytest` | Runs the no-key tests and the release gate (`gate.sh`, `gate.yml`). | A hand-rolled test runner. |
| `ruff` | The linter the release gate runs before every push. | No lint step. |
