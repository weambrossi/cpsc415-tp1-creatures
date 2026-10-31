# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
Team Project 1 for CPSC 415: a web app that generates images of original pocket creatures from a
text description, displays them, and critiques each one with a vision model that reads the image.
The critique is checked in plain code. See [`spec.md`](spec.md) and [`plan.md`](plan.md).

## Commands
```
# setup   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# test    .venv/bin/python -m pytest            (model tests skipped without OPENROUTER_API_KEY)
# lint    .venv/bin/ruff check .
# gate    sh .git/hooks/pre-push                (ruff + no-key tests; runs on every push)
```

## Conventions
- Python 3 in `.venv`. Dependencies are named in `spec.md` with the reason before they go in
  `requirements.txt`; the guard blocks installs that `spec.md` does not list.
- Tests in `tests/test_*.py`. Tests that call a model are marked and skipped when no key is set.
- Branches are `week06-<name>` or `<feature>-<name>`; every change reaches `main` through a
  pull request reviewed against `REVIEW.md` and approved by a teammate.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.
- Image generation and vision calls are billed. One generation per prompt, one critique per image,
  fixed seeds. Never loop over the model inside a test.
- The critique is model output. The code compares it with the requirements; it does not trust it.
- Prompts describe original creatures in a creature-collector style. Never name an existing
  franchise, character, or real person.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
- Never read `.env`; check whether a key is set with `test -n "$OPENROUTER_API_KEY"`.
