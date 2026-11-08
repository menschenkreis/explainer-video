---
name: explainer-video
description: Build narrated explainer videos as CODE (HTML/CSS/JS timeline locked to an ElevenLabs voice-over) from study material such as a PDF chapter, script or notes. No AI video generation. Use when the user wants explainer / learning / lecture videos with animated diagrams that are timed to narration, or says "code the video", "make an explainer from this chapter", "video from the PDF". Output is one self-contained index.html (plus narration.mp3) that plays in any browser and can be exported to MP4.
---

# explainer-video

Videos are **coded, not generated**. A scene is HTML/SVG/CSS; one deterministic function `render(t)` draws
every frame; the narration audio is only the clock. Because each animation is keyed to a *word* in the
script (`[cue]` markers), picture and voice cannot drift. ElevenLabs is used for the voice only.

```
source (PDF/notes) ──► script.md  (spoken text with [cue] markers, one ## section per scene)
                          │ narrate.py   ElevenLabs with-timestamps → narration.mp3 + build/timing.json
scenes/NN-id.html ────────┤ build.py     engine + scenes + timing → index.html  (validates cues)
                          │ shot.py      screenshots at cue times (verify without watching)
                          └ render_mp4.py frame-exact export, narration muxed in
```

## One-time setup
```bash
~/.claude/skills/explainer-video/ev setup     # helper venv (pymupdf + playwright; uses your installed Chrome)
~/.claude/skills/explainer-video/ev doctor    # checks python, ffmpeg, Chrome, ElevenLabs key
~/.claude/skills/explainer-video/ev key       # saves the ElevenLabs key (hidden prompt)
```
`ev` wraps every script below (`ev new|preview|narrate|build|shots|mp4|all|site|voices|extract`); the raw scripts in
`scripts/` stay available. In the commands below `$EV` = this skill's `scripts/` folder, `$PY` = the helper venv python.
ElevenLabs key: environment variable `ELEVENLABS_API_KEY`, or a line `ELEVENLABS_API_KEY=…` in `./.env` or
`~/.config/explainer-video/.env`. **Never ask the user to paste the key into chat, never print it.**
Pick a voice with `python3 $EV/narrate.py --list-voices`, put `voice_id:` in the script front matter
(or `ELEVENLABS_VOICE_ID`). Let the user choose by ear before spending a whole video on it
(`--only <scene>` renders a single scene).

## Workflow
1. **Scaffold** `python3 $EV/new_project.py videos/<slug> "<Title>"` (script.md + a sample scene).
2. **Read the source.** `$PY $EV/extract_chapter.py book.pdf --find "3.1 Heading" --until "3.3 Next"` or
   `--pages 130-162 -o build/source.txt`; then read the text. OCR text around figures is noisy – rebuild diagrams
   from the prose and captions, cite page numbers.
3. **Storyboard first**, then `script.md`. See `references/storyboard-guide.md`. Budget: German ≈ 14.5 chars/s,
   i.e. **~870 characters per minute**. Aim for 8–10 min per video; **split long chapters into parts** rather than
   cramming (a 17k-character script is ~19 min). Check with `narrate.py script.md --estimate`.
4. **Author scenes** – one fragment per scene in `scenes/NN-id.html`, elements tagged `data-at="cue"`
   `data-fx="rise|pop|draw|…"`. API in `references/engine-api.md`. Reuse the patterns in the guide (matrix, network
   with auto-routed arrows, phase ribbon, charts that draw themselves, swim-lanes, cycles with loop arrows, cards).
5. **Preview without credits**: `python3 $EV/narrate.py script.md --estimate && python3 $EV/build.py` → open
   `index.html` (silent, estimated timing, captions on). `build.py` fails on any cue used in markup but missing in the
   script and warns about unused cues.
6. **Verify visually** (do this, don't guess):
   `$PY $EV/shot.py index.html --all-scenes --sheet` (end state of every scene) and
   `--scene <id> --sheet` (one frame ~1 s after each cue = the build-up). `Read` the PNGs. Fix overlap, clipping,
   wrapping. Console warnings/missing cues are printed.
7. **Narrate** (costs credits): `python3 $EV/narrate.py script.md --dry-run` shows the character count; then run it
   without flags. Every scene is cached by content hash, so re-runs only pay for edited scenes. Re-run `build.py`.
   Spot-check sync again with `shot.py --scene …`. You cannot hear audio – say so; ask the user to listen
   (pronunciation of names, numbers, pauses).
8. **Deliver**: `index.html` + `narration.mp3` together (relative path). Optional MP4:
   `$PY $EV/render_mp4.py index.html -o video.mp4 --workers 4 [--captions]` (~25 fps per worker; test an excerpt with
   `--start 60 --end 70`).

## Rules that matter
* **One idea per scene, 30–70 s.** Every sentence either triggers a visual or is part of one build-up.
* **Cue = the word the visual should land on.** Put `[cue]` right before it. Cue names: letters/digits/underscore only.
  Stagger list items with offsets (`cue+1.8`) inside the time the sentence takes.
* **Spoken text ≠ slide text.** Write numbers/abbreviations the way they should be pronounced (“zwei bis fünf Prozent”,
  “B M W”, section numbers go in the on-screen kicker, not in the narration). German: Swiss spelling (ss, no ß) when
  the user is Swiss.
* **Paraphrase, don't copy** book text (copyright); cite chapter/page on screen or in script notes (`> note`).
  Mark schematic redraws “schematisch nach Abb. x.y” so they aren't mistaken for the original figure.
* **Match the user's language** to the source/exam language by default; confirm if unclear.
* Text on screen ≥ 24 px (stage is 1920×1080), ≤ ~25 words per card. Captions are on by default (`CC` button).
* Never put work in `/tmp` – keep project folders under the user's chosen folder; the scratch workspace is deleted
  with the session.
* This skill is *not* ComfyUI/AI-video generation. If the user wants generated footage, use the `comfy` skills.

## Gotchas already hit (don't repeat)
* An element with both `.graph` and `.abs` must stay absolutely positioned (fixed in theme.css; keep `.graph.abs`).
* `data-fx="hl"` is ring+glow only; use `hlfill` when you want a background wash, never put an opaque highlight
  overlay over text.
* SVG text/shapes outside the `viewBox` are clipped unless `style="overflow:visible"`.
* Edge endpoints need `id`s that are unique across the whole video (prefix with the scene id).
* Don't name two cues the same inside one scene; cue keys are `sceneid.cue`.
* Frame screenshots are the only way to see layout problems: long German words wrap – add `&shy;` hints.
* ElevenLabs `with-timestamps` returns characters of the *input* text; the script strips markers first, so indices match.

## Files
`engine/` theme.css · engine.js · player.html (copied into every build) — `scripts/` narrate · build · shot ·
render_mp4 · extract_chapter · new_project · mock_elevenlabs (test double for the API) — `references/` engine-api ·
script-format · storyboard-guide.
