# Storyboard & scene guide

## From source chapter to scenes
1. List the chapter's headings; each sub-section (or two small ones) becomes a scene. Keep the book's numbering on the
   screen (`.kick`), not in the narration.
2. For every scene write **one sentence of takeaway** first. If you can't, the scene is a list – turn it into a
   comparison, a flow, a matrix or a chart, or merge it.
3. Decide the visual per scene *before* writing narration: what appears, in which order. Then write narration so the
   order of sentences equals the order of build-up, and drop a `[cue]` before the word each element should land on.
4. Length: ~870 chars/min (German). 30–70 s per scene, 8–10 min per video. A whole chapter usually needs 2 parts;
   put an intro scene (where are we in the model) and a recap scene (4–5 take-aways + pointer to the book's self-test)
   in each part.
5. Faithfulness: reproduce the book's terms, numbers and examples; label schematics; don't invent facts. Keep a
   source note (`> S. 138: …`) next to doubtful passages in script.md.

## Visual patterns that worked
| need | pattern |
|---|---|
| model hierarchy | `.graph` nodes + auto-routed `edge`s, each node on its cue |
| element × relation categories | generated CSS grid, cells glow (`hlfill`) at cues |
| scope / boundary | concentric circles (`pop`), bars (`grow`) for the trade-off |
| cause-and-effect network | many nodes with staggered offsets, then edges |
| five principles | five cards + tiny SVG icons that draw (`draw`/`wipe`) |
| process phases | chevron ribbon (`left` stagger), gates as diamonds |
| quantitative curve | SVG paths with `draw`, shaded bands with `fade` |
| schedule / overlap | Gantt bars with `growx` |
| 2×3 matrix of levels | grid + coloured focus outlines (`fade`) |
| cycle with loops | vertical flow + curved edges (`data-curve`) for back-jumps |
| roles / swim-lanes | two lane bands + nodes + edges across lanes |
| take-aways | 2×2 cards on `r1…r4` cues |

## Layout rules
* Body 1728×780. Leave ≥ 24 px gaps, keep fonts ≥ 24 px, card text ≤ ~25 words. Long German compounds: add `&shy;`.
* Use colour consistently: `cc` blue = given/model, `ca` amber = focus/current, `cb` teal = process/positive flow,
  `cd` coral = problem/risk/back-jump, `cok` green = take-away/check, `ce` violet = third category.
* Bring the picture before the explanation: elements land on or just before the word they illustrate.
* A scene with a long enumerated sentence: give each item its own offset (`cue+0.8, +2.6, +4.4`) – roughly where the
  words fall; check with `shot.py --scene id --sheet` after the real narration and adjust offsets, or add more cues.
* Rule of thumb for stagger offsets: German speech ≈ 2.4 words/s.
* Estimated-mode previews are for layout; **re-run `shot.py` after real narration** because cue times move.

## Checklist before declaring a video done
- [ ] `build.py` prints no ERROR / unused-cue warnings
- [ ] `shot.py --all-scenes --sheet` reviewed: no overlap, clipping, unreadable text
- [ ] `shot.py --scene <id>` reviewed for the 3 most complex scenes (build-up order matches narration)
- [ ] narration listened to by the user (names, numbers, pacing); weak scenes re-generated with `--only`
- [ ] total length matches the goal; outro/recap present
- [ ] `index.html` + `narration.mp3` (and optional `video.mp4`) saved in the user's folder, not in scratch
