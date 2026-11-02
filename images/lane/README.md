# Lane's image set

Five creatures from one prompt family (`prompts/lane.json`): one fox kit adapted to five habitats
(forest, desert, ocean, city, snow), in the team style text word for word, so the same prompts come
out of `app.generator.build_prompt`. Seeds 6301–6305, generated once on
`black-forest-labs/flux.2-klein-4b` on November 2, 2026, $0.014 each (`manifest.json` records
prompt, seed, model, media type, and cost per image). Each image has the four shared requirements
plus two of its own.

`critique.json` is `minimax/minimax-m3`; `critique-mimo.json` is `xiaomi/mimo-v2.6-flash` (reasoning
off). Both critics read REEFKIT's banner back as "REFKIT", so the code reports a name mismatch on
that image. The two critics disagree on one image, REEFKIT: MiniMax's checklist says the banner
and the no-other-text requirements are met, MiMo's says they are not. MiniMax's own narrow name
read disagrees with its checklist, which is why the code trusts the narrow read, not the checklist.

Full record (costs, what I saw in each image, the seed check, the Gemini comparison, and which
check caught what): `week06/CHECKS.md` in my Week 5 repository,
[lanefaison1-del/cpsc415-week05](https://github.com/lanefaison1-del/cpsc415-week05/blob/main/week06/CHECKS.md).
