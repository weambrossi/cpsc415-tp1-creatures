# Intent: creature generator

## Goal
Given a short description a fan types ("a professor owl") and a one-word name ("PROFOWL"), the app
produces one picture of an original pocket creature in a fixed game-art style, with the name in a
banner at the top, and records exactly what was asked for and what it cost.

## Who it is for
Fans designing their own creature-collector monsters, through the web page Lane builds, and the
critic-checker Joud builds, which needs to know what each image was asked to show. Today a fan
would use a general image tool that drifts from the style, adds extra characters or stray text,
and misspells names, with no record of the prompt, seed, or cost.

## Constraints
- Python 3, in the team `.venv`; the `openrouter` SDK for the Image API.
- `black-forest-labs/flux.2-klein-4b` by default (about $0.014 per image), with
  `google/gemini-3.1-flash-lite-image` as the compared alternative.
- One generation per request, fixed seed, no automatic retries.
- Prompts describe original creatures; never an existing franchise, character, or real person.
- Every image's prompt, seed, model, media type, and cost from the reply are recorded.
- The key comes from `OPENROUTER_API_KEY` in the environment; it never reaches the browser or a commit.
- Tests come before code; no test calls the model.

## Not in scope
The critique (Joud), the web page and server (Lane), regenerating a failed image, choosing the
best of several images, user-uploaded photos, and audio.

## Success looks like
- `build_prompt("a professor owl wearing round glasses", "PROFOWL")` returns a full prompt in the
  team style, the shared requirements, and `expected_text` "PROFOWL", with no model call.
- `python -m app.generator prompts/ethan.json --out images/ethan` makes five images and a
  `manifest.json` with prompt, seed, model, media type, and cost for each.
- Ethan's five-creature set and its critiques from the Week 6 lab are in `images/ethan/`.

## Open questions
None blocking. The Week 6 lab settled the style text, seeds, and the comparison model's result.

**Approved by:** Ethan Ambrossi, 2026-10-31
