# Spec

<!-- The agent writes this from the approved intent. You validate it against the intent.
     If the spec and the intent disagree, the intent wins until you change the intent. -->

## Intent
Which `intent/*.md` file(s) this spec implements.

## Components
One entry per component. Two design decisions are required for each.

### <component name>
- **What it does:**
- **Language:** <language>. **Why:** alternatives considered and the trade-off. Java and Python are both permitted; unfamiliar-language practice is a separate guided exercise.
- **Model:** <vendor/model-slug>. **Why:** what you compared it against (at least one cheap model versus one frontier model on a real task) and what differed.
- **Interfaces:** inputs, outputs, files, endpoints.
- **Dependencies:**

## Behavior
Requirements the tests will check. Number them.

1.
2.

## Failure handling
What happens on bad input, a refused or hallucinated model response, a missing key, a timeout.

## Cost estimate
Tokens or calls per use, and what a semester of use costs at the chosen model's price.

## Out of scope
Carried over from the intent, plus anything the design ruled out.

## Dependencies (repository-wide)
| Package | Why | By hand it would be |
|---|---|---|
| `openrouter` | The official OpenRouter SDK: `client.images.generate` for the Image API and `client.chat.send` for the vision critique, one client object for both request shapes. | Two hand-built `urllib.request` calls with manual JSON, base64 and error handling, as in Weeks 2–5. |
| `pytest` | Runs the no-key tests and the release gate (`gate.sh`, `gate.yml`). | A hand-rolled test runner. |
| `ruff` | The linter the release gate runs before every push. | No lint step. |
