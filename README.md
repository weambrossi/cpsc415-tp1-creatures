# Artifact-chain template

Starting point for major project submissions in CPSC 415 (AI Integration, Trinity College). Click **Use this template** on GitHub to create your own repository from it. Do not fork.

The course follows Anthropic's [AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook): every stage of the work leaves a short, version-controlled artifact. The agent writes most of the code. You decide what gets built, steer, verify, and explain every choice. These files are how you prove you understood what the agent built.

## Early labs

Week 1 uses the minimal repository described in the course handout. Later introductory labs complete only the stages assigned so far. This template describes the full chain for team projects and the final portfolio; it does not require unintroduced artifacts in Week 1. Project languages are chosen and justified, with one separate guided exercise in an unfamiliar language.

## The chain

| Stage | File | Written by | Approved by |
|---|---|---|---|
| Plan | `intent/<name>.md` | The agent, after interviewing you | You |
| Design | `spec.md` | The agent, from the approved intent | You, against the intent |
| Build | `plan.md`, then code on a branch | The agent | You, before any code |
| Test | tests, lint, CI | The agent | You confirm the loop actually ran |
| Deploy | a pull request reviewed against `REVIEW.md` | A separate reviewing agent | You merge |
| Maintain | a new `intent/<name>.md` | Triggered by a bug, a ticket, or a model change | You triage |

`CLAUDE.md` and `REVIEW.md` travel with the repo and are graded artifacts.

## Rules that are graded

- Intent and spec exist before code. Plan is approved before implementation. The commit history shows it.
- One pull request per feature, from a branch, reviewed before merge. Do not commit to `main` directly after the first commit.
- `spec.md` states the **language** and the **model** for each component and why.
- `ANNOTATION.md` answers the four questions for the finished project.
- No secrets in the repo. `.claude/settings.local.json` and `.env` are ignored; the `.example` file shows the shape.

## Submitting

Tag the commit you are submitting and put the repository URL plus the tag on Moodle:

```
git tag tp1-submitted
git push origin tp1-submitted
```

Tags the course uses: `intent-spec`, `tp1-submitted`, `tp2-submitted`, `portfolio-final`.

## Running the agent

Copy `.claude/settings.local.json.example` to `.claude/settings.local.json` and fill in your OpenRouter key and model slugs, or use the `orclaude` launcher from the [course repository](https://github.com/kousen/ai-integration-course/tree/main/scripts).

## Cost so far

Every billed call in TP1, from the repo's own records (`manifest.json` and the critique files), then checked against each member's OpenRouter usage page before submission.

| Member | Images | Critique (minimax) | Critique (MiMo) | Recorded total | Usage page |
|---|---|---|---|---|---|
| Ethan | 5 × $0.014 = $0.0700 | $0.0060 | $0.0015 | $0.0775 | _pending_ |
| Joud | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| Lane | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| **Team** | | | | **$0.0775 so far** | |

The Week 6 labs (about $0.15 to $0.25 each, in each member's own `cpsc415-week05`) are not in this table. On Ethan's set MiMo cost a quarter of what minimax did per critique: $0.0003 against $0.0012 per image.

## Provenance

Checked in the image bytes, not taken from a vendor page.

**FLUX.2 klein** (`black-forest-labs/flux.2-klein-4b`, the generator's model). Every JPEG carries an embedded C2PA manifest (content credentials, `c2pa.claim.v2`). It is signed by Black Forest Labs Inc. with a GlobalSign certificate and timestamped by DigiCert. The manifest records a `c2pa.created` action with digital source type `trainedAlgorithmicMedia` (the IPTC term for AI-generated), a `c2pa.ai-disclosure` assertion naming the model as "FLUX.2 [klein]", the generator as "Black Forest Labs API", and the creation time. There is no EXIF or XMP. All five of Ethan's images have one, each with its own `urn:c2pa` id.

Two limits. C2PA is metadata: a screenshot, a re-encode, or most upload pipelines strip it, and the image then carries no claim at all. And the manifest says who made the file, not what the prompt was; that lives only in our `manifest.json`.

**Gemini** (`google/gemini-3.1-flash-lite-image`, the comparison model). Not checked: the comparison image is in Ethan's Week 5 repository, not here.

To check an image yourself, look for the `c2pa` JUMBF box: `grep -c c2pa images/ethan/profowl.jpg`, or open it at [contentcredentials.org/verify](https://contentcredentials.org/verify).
