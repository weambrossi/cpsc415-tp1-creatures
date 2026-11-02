# Intent: critic-checker

## Goal
After the generator makes a creature, a vision model looks at the picture and answers each of its
requirements yes or no, and plain code decides whether the picture passes. The model's answer is
treated as a claim to check, never as the verdict.

## Who it is for
Fans using Lane's page, who want to know what came out wrong without squinting at every image, and
the team, who need a record of which images failed and why. Today the only check is a person
looking at each image, which misses a misspelled banner (the October 19 "Integratlon" case).

## Constraints
- Python 3, in the team `.venv`; the `openrouter` SDK's chat endpoint with the image as a data URL.
- `minimax/minimax-m3` by default (about $0.001 per checklist on Ethan's set), checked against
  `xiaomi/mimo-v2.6-flash` as the second critic.
- Reads the generator's manifest as is: `prompt`, `requirements`, `expected_text`, `file`,
  `media_type`. No second copy of the generator.
- One checklist call and one text-reading call per image. No retries, no loop over the model in a test.
- The name in the banner is compared in code against `expected_text`. The critic never decides it.
- A reply that is not the JSON asked for is a failed critique, not a crash.
- Tests come before code; no test calls the model.

## Not in scope
Generating or regenerating images (Ethan), the page and server (Lane), scoring style or beauty,
choosing the best of several images, and fixing a failed image.

## Success looks like
- Given a critique that skips a requirement, invents one, or answers `"yes"` instead of `true`, the
  checker says so by name, with no model call.
- `python -m app.critic images/joud/manifest.json` writes `critique.json`, and the same run with
  `--model xiaomi/mimo-v2.6-flash --out images/joud/critique-mimo.json` writes the second file.
  `--compare` lists every image where the two critics disagree.
- Lane's server can call one function with image bytes and get back a pass or fail with each
  problem named.

## Open questions
None blocking. Which critic is stronger is settled by the comparison on Joud's five images.

**Approved by:** Joud Bitar, 2026-11-02
