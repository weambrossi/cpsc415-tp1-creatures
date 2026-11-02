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
It looks at each creature and reports what came out wrong. For every image in the manifest it makes
two calls to a vision model through OpenRouter: one answers each of the image's requirements with
true or false and a line of evidence, and one reads the name off the banner. Then code decides. It
checks that the checklist covers exactly the requirements the generator asked for, with real
booleans, and compares the name the model read against `expected_text`. It does not make or fix
images, judge whether a creature looks good, or pick the best of several.

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
A model will say an image passes even when it is wrong, so I treat its answer as a claim and code
has the last word. Code can't see the picture, but it can catch a skipped requirement, an invented
one, a "yes" string where it wanted `true`, and a misspelled name. The name check came from October
19, when a person looking at the images missed "Integratlon" on a banner. I used two critics because
one model misreading looks the same as a real failure. MiniMax M3 is the default and cost $0.0081 on
my five images; MiMo v2.6 flash cost $0.0018. Python, because Ethan's generator and Lane's server
are Python.

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
The critic can misread the name, and the code trusts what it read. On ZAPPLUME the banner is spelled
right, but MiniMax read "ZAPLUME" and failed the image while MiMo passed it. `--compare` flagged it
because the two disagreed, but if both models misread the same way, nothing flags it. The checklist
has the same weakness: code checks that every requirement got an answer, and it has no way to know
if "met: true" is true. A pass only means the model said yes to everything and the name it read
matched, so someone still has to look at the failures.

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
The parser broke on a correct answer. The reviewing agent found that `extract_json` grabbed
everything from the first `{` to the last `}`, so a stray brace in the model's prose turned a valid
checklist into a failed critique. It's fixed now with `raw_decode` and three tests. I also learned
to read `finish_reason`: before the fix, a reply cut off at "length" could still pass, and now it
counts as a failed critique. And the model I picked as the default was the one that misread
ZAPPLUME, which I wouldn't have known without running a second one.

### Web app (Lane)
_To be written by Lane._
