# Intent: web app

## Goal
A page on my laptop where a fan types a short description and a one-word name, clicks
**Generate**, sees the creature, and then sees the critique: each requirement marked met or not,
each problem named, and whether the name in the banner was read correctly. The server holds the
OpenRouter key; the browser never sees it.

## Who it is for
Fans designing their own creatures, and our team at the November 2 presentation, where the app
runs live. Without it, generating and critiquing a creature means running two command-line
programs and reading JSON files.

## Constraints
- Python 3.11 in the team `.venv`, Flask for the server, Playwright for the browser check.
- The key comes from `OPENROUTER_API_KEY` on the server only: never in the page, in a request
  the browser makes, or in a commit.
- The server calls Ethan's generator and Joud's critic-checker. It holds no second copy of
  either, and the page cannot choose a model, so a visitor cannot pick a more expensive one.
- One generation and one critique per click, a fixed default seed, no retries.
- Original creatures only; the generator's name and franchise rules apply unchanged.
- Runs on localhost. Ready before the 1:30 PM presentation on November 2, 2026.

## Not in scope
Hosting, accounts, a saved gallery, regenerating or editing an image, uploading a photo, audio,
and the critic's own logic (Joud's).

## Success looks like
- Typing "a small forest fox kit holding an acorn" with the name FERNKIT shows the image, then
  a checklist with a mark for every requirement and the banner name read back.
- A name the generator refuses ("FERN KIT") or a franchise word shows the generator's message on
  the page, and nothing is billed.
- The browser test passes: it finds no `sk-or` in the page or in any request, no request from
  the browser to openrouter.ai, and calls to our own `/api/generate` and `/api/critique`.

## Open questions
None blocking. Joud's PR #3 defines `critique_one(client, model, image_bytes, media_type, prompt,
requirements, expected_text)`, and the server calls exactly that. Until his PR merges, the
critique step says the critic-checker is not merged yet.

**Approved by:** Lane Faison, 2026-11-02
