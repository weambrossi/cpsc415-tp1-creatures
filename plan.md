# Plan

<!-- The agent proposes this from the spec. Interrogate it ("what could break?") and approve
     before any code is written. Update it when the plan changes. -->

Team Project 1, Pocket Creatures: a fan types a short description, the app generates an original
creature image with its name in a banner, and a vision model critiques the image against a yes/no
checklist that plain code checks. Due Monday, November 2, 2026, 1:30 PM, with each member's
Week 6 lab. Team: Ethan Ambrossi, Joud, Lane.

## Who does what

**Agent: read this section before doing anything in this repository.**

1. If the person has not said who they are, ask: "Are you Ethan, Joud, or Lane?"
2. Work only on that person's tasks below, in order. Start at their first unchecked task.
   Check a task off (`[x]`) in this file in the same commit that finishes it.
3. Work on that person's branch: `week06-ethan`, `week06-joud`, or `week06-lane`, created from an
   up-to-date `main`. Never commit to `main`. The plan PR uses `plan-ethan`.
4. Edit only the files that person owns (the **Owns** line). In `spec.md`, edit only their
   component's section. If a task needs another person's file, say so and stop.
5. If a task is blocked on someone else's PR, say which one and offer the person's unblocked work
   (for Lane: build the page against fake data in `tests/fakes.py`).
6. Intent first (interview one question at a time, then `intent/<name>.md`), then the spec
   section, then tests before code: run the tests so the person sees them fail, then write the
   code. Stop after each step.
7. Never do these; they belong to the person: sign an **Approved by** line, approve or merge a PR,
   submit on Moodle, write their `ANNOTATION.md` answers, or run the open-ended critique in Week 6
   lab step 5.2.
8. Billed calls: one generation per prompt, one critique per image, fixed seeds, never inside a
   test loop. Tests that call a model are marked and skipped when no key is set.

### Ethan: setup, generator, PR 1 (goes first; the others build on it)
**Owns:** `plan.md`, `CLAUDE.md` (except Commands for the server), `intent/generator.md`,
`spec.md` Generator section, `app/generator.py`, `tests/test_generator.py`, `prompts/ethan.json`,
`images/ethan/`, `ANNOTATION.md` Generator section.

- [x] E1. Team repo from the course template: guard, `requirements.txt`, conventions, pre-push gate.
- [x] E2. Add Joud and Lane as collaborators on GitHub (joudbitar, lanefaison1-del invited Oct 31).
- [ ] E3. This plan, approved by Ethan, merged through PR `plan-ethan`; Joud approves.
- [x] E4. `intent/generator.md` (approved by Ethan) and the Generator section of `spec.md`:
      language Python; model `black-forest-labs/flux.2-klein-4b`, compared with
      `google/gemini-3.1-flash-lite-image`, with cost and seed results from the Week 6 lab.
- [ ] E5. Week 6 lab steps 1–5 in Ethan's own `cpsc415-week05` (family: PROFOWL, STUDEX,
      BOLTBIT, CHEFROG, DASHELL).
- [ ] E6. PR 1, branch `week06-ethan`: `app/generator.py` (prompt → Image API → saved image +
      `manifest.json` with prompt, seed, model, media type, cost), no-key tests first,
      `images/ethan/` + `prompts/ethan.json`. Gate, `review.py`, findings as a PR comment, fix or
      answer every pass-1/pass-2 finding. **Joud approves**, then merge.
- [x] E7. `ANNOTATION.md` Generator section, written by Ethan.
- [ ] E8. After PR 3 merges: tag `tp1-submitted`, push it, submit repo URL + tag on Moodle.
      Tag own `cpsc415-week05` `week06-submitted` and submit the Week 6 lab.
- [ ] E9. Presentation outline: live demo, one chain artifact on screen, one failure and the fix.

### Joud: critic-checker, PR 2 (after PR 1 merges)
**Owns:** `intent/critic.md`, `spec.md` Critic-checker section, `app/critic.py`,
`tests/test_critic.py`, `prompts/joud.json`, `images/joud/`, `README.md` cost total,
`ANNOTATION.md` Critic-checker section.

- [ ] J1. Clone, `python3 -m venv .venv`, `.venv/bin/pip install -r requirements.txt`, install
      the gate (`cp <course repo>/examples/pr-review/gate.sh .git/hooks/pre-push`, then
      `chmod +x`, then add `PATH="$(pwd)/.venv/bin:$PATH"` after its `cd` line), and check the
      guard blocks `git push --force`.
- [ ] J2. Review and approve the plan PR and PR 1.
- [ ] J3. `intent/critic.md` (approved by Joud) and the Critic-checker section of `spec.md`:
      language Python; model `minimax/minimax-m3`, checked by `xiaomi/mimo-v2.6-flash` (the
      cheap-vs-stronger comparison TP1 requires). Numbered behaviors: a critique that is not JSON
      is a failed critique, not a crash; an unanswered requirement is a problem; an invented
      requirement is a problem; the name text is compared in code, not by the critic.
- [ ] J4. Week 6 lab steps 0–5 in Joud's own `cpsc415-week05` (family: one creature per element:
      fire, water, leaf, stone, storm).
- [ ] J5. PR 2, branch `week06-joud`, built on the merged generator (no second copy):
      `app/critic.py` (checklist from requirements, JSON extraction, checker, compare two
      critique files), no-key tests first (all met, one unmet, unanswered, invented, not JSON,
      JSON in prose, name mismatch, two critics disagreeing), `images/joud/` with manifest and both
      critique files. Gate, reviewer, PR comment, fixes. **Lane approves**, then merge.
- [ ] J6. `ANNOTATION.md` Critic-checker section, written by Joud.
- [ ] J7. `README.md`: running cost total from each member's OpenRouter usage page, and what
      provenance each image model's output carries.
- [ ] J8. Tag own `cpsc415-week05` `week06-submitted`; submit PR 2 URL + repo URL on Moodle.

### Lane: web app, PR 3 (starts now on fake data; wires real modules after PR 2)
**Owns:** `intent/web-app.md`, `spec.md` Web app section, `app/server.py`, `static/`,
`tests/test_server.py`, `tests/test_browser.py`, `tests/fakes.py`, `prompts/lane.json`,
`images/lane/`, `CLAUDE.md` Commands for the server, `ANNOTATION.md` Web app section.

- [ ] L1. Clone and set up (same as J1).
- [ ] L2. `intent/web-app.md` (approved by Lane) and the Web app section of `spec.md`: language
      Python; framework Flask vs standard-library `http.server` (see the course's
      `examples/key-on-server`); the key stays on the server; `flask` and `playwright` named under
      Dependencies before they are installed (the guard blocks them otherwise).
- [ ] L3. Week 6 lab steps 0–5 in Lane's own `cpsc415-week05` (family: one creature in five
      habitats: forest, desert, ocean, city, snow).
- [ ] L4. Review and approve PR 2.
- [ ] L5. PR 3, branch `week06-lane`: `app/server.py` (`POST /api/generate` → generator,
      `POST /api/critique` → critic, key from the environment only), `static/index.html` (text box,
      image, checklist result with each problem named), `tests/test_browser.py` with Playwright
      (type a description, see an image and a critique, no `sk-or` in the page or requests).
      Build first against `tests/fakes.py`, then swap in the real modules once PR 2 merges.
      Gate, reviewer, PR comment, fixes. **Ethan approves**, then merge.
- [ ] L6. `ANNOTATION.md` Web app section, written by Lane.
- [ ] L7. `CLAUDE.md` Commands: how to run the server and the browser test.
- [ ] L8. Tag own `cpsc415-week05` `week06-submitted`; submit PR 3 URL + repo URL on Moodle.

## Files to create or change
| File | Purpose | Owner |
|---|---|---|
| `intent/generator.md`, `intent/critic.md`, `intent/web-app.md` | One intent per major feature | Ethan, Joud, Lane |
| `spec.md` | One section per component: language and model decisions, behaviors | each owner |
| `app/generator.py` | Prompt → OpenRouter Image API → image + `manifest.json` | Ethan |
| `app/critic.py` | Image + checklist → vision model → JSON → checked in code | Joud |
| `app/server.py`, `static/index.html` | Web app; holds the key, serves the page | Lane |
| `tests/` | No-key tests per module; browser-driven check | each owner |
| `prompts/<name>.json`, `images/<name>/` | Each member's five-prompt family, images, manifest, critiques | each owner |
| `README.md` | How to run; running cost total | Joud |
| `ANNOTATION.md` | Four questions per component, written by its owner | each owner |

## Order of work
1. Plan PR merged (Sat Oct 31).
2. Everyone: intent + spec section + own Week 6 lab steps 0–5 (Sat–Sun). Lane builds the page on fakes.
3. PR 1 generator merged (Sun Nov 1).
4. PR 2 critic-checker merged (Sun Nov 1).
5. PR 3 web app merged (by Mon Nov 2 morning).
6. `ANNOTATION.md`, `README.md` cost, `tp1-submitted` tag, Moodle (Mon Nov 2, before 1:30 PM).

## Risks
- **PR 1 slips and blocks PR 2 and PR 3.** Lane works on fakes; Joud's checker tests need no
  generator. If PR 1 is not merged by Sunday noon, Joud and Lane branch from `week06-ethan`.
- **Merge conflicts in `spec.md` and `CLAUDE.md`.** Each person edits only their own section;
  rebase on `main` before pushing.
- **The critic is wrong** (the October 19 "Integratlon" case). The checker compares the name in
  code and a second model checks the critic; a person looks at every disagreement.
- **Cost.** Each member's lab is about $0.15–0.25; one demo run is about $0.02. A test that loops
  over the model would multiply that; tests never call a model in a loop.
- **No teammate available to approve.** Open the PR anyway; the PR URL is what Week 6 needs.

## Proof
- No-key tests for each module and the gate on every push (`ruff check .` + `pytest` without a key).
- `review.py` exits 0 on each PR, with its findings posted as a PR comment.
- `tests/test_browser.py` drives the page in a real browser.
- Each member's `week06/CHECKS.md` records costs, verdicts, the seed check, and the Review section.

## Subagents and parallel work
None. The three members' work runs in parallel on separate branches and separate files.

**Approved by:** Ethan Ambrossi, 2026-10-31
