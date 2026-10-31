# Four-question annotation

<!-- Required for every project in the portfolio and every team project.
     Written by you, not the agent. This is what the Comprehension Defense asks about.
     One subsection per component, each written by its owner. -->

## What is this?
A plain statement of what it does and does not do.

### Generator (Ethan)
It makes the creature image and saves what it cost. Given a description and a name,
`build_prompt` wraps them in the team's style text, `generate_one` makes one call to FLUX.2 klein
through the OpenRouter Image API, and `run` saves each image with a `manifest.json` recording the
prompt, seed, model, media type, and the cost from the reply. It does not critique the image or
regenerate one that came out wrong; that is the critic-checker's job to report.

### Critic-checker (Joud)
_To be written by Joud._

### Web app (Lane)
_To be written by Lane._

## Why this choice?
What alternatives existed, including language and model, and what trade-offs were weighed.

### Generator (Ethan)
FLUX was cheaper, and Gemini added extra text. On the same prompt and seed (PROFOWL, 6101), FLUX.2
klein cost $0.014 and met every requirement; `google/gemini-3.1-flash-lite-image` cost $0.0336
and printed "ARCANE KNOWLEDGE" on the owl's book, breaking "no text other than the name". Python,
because the OpenRouter SDK and the critic and server that import the generator are Python.

### Critic-checker (Joud)
_To be written by Joud._

### Web app (Lane)
_To be written by Lane._

## What breaks?
Fragile points, assumptions, blast radius.

### Generator (Ethan)
It can misspell the name: all five of my names came out right, but image models get text wrong
often, so the critic-checker has to compare the name in code. The word filter is easy to get
around: it blocks names like "pokemon" or "pikachu", but a description such as "a yellow electric
mouse" gets through.

### Critic-checker (Joud)
_To be written by Joud._

### Web app (Lane)
_To be written by Lane._

## What did I learn?
Concretely. Include places where the agent was confidently wrong and you caught it.
What did you learn about reading code or using concepts that were unfamiliar to you?

### Generator (Ethan)
The reviewer said a test would fail, and it didn't. On the plan PR, the reviewing model claimed
`test_repo.py` would break on capitalization, but the test lowercases both sides and passed in the
gate, so I answered the finding on the PR instead of changing the code. A reviewer's findings are
a list to check against the code, not a verdict.

### Critic-checker (Joud)
_To be written by Joud._

### Web app (Lane)
_To be written by Lane._
