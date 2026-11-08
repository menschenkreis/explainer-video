# script.md format

```markdown
---
title: Systems Engineering – Systemgestaltung anwenden
lang: de
model: eleven_multilingual_v2      # eleven_v3 for expressive reading (audio tags), multilingual_v2 for steady explainer voice
voice_id: xxxxxxxx                 # or env ELEVENLABS_VOICE_ID / --voice
stability: 0.5                     # 0–1, lower = more expressive
similarity: 0.75
style: 0
speed: 1.0                         # optional, 0.7–1.2
lead: 0.7                          # silence before each scene's speech (visuals appear first)
gap: 0.7                           # silence after each scene
tail: 2.0                          # extra hold after the last scene
---
> Lines starting with ">" are notes (source pages, TODOs) and are never spoken.

## intro | Einstieg: Systemgestaltung
Spoken text, one paragraph or several. [philo] The animation tagged `philo` fires on the next spoken word.
[denken] Markers can sit anywhere; they are removed before the text goes to ElevenLabs.
```

* `## id | Title` – `id` = scene id (letters/digits/underscore) = `data-scene` in the fragment; Title shows in the scene menu.
* `[cue]` – letters, digits, underscore. Becomes `id.cue` on the timeline with the start time of the next
  non-space character, taken from ElevenLabs' character alignment.
* Scenes are synthesised separately (cached by hash of text+voice+model+settings in `build/audio/`), with the
  neighbouring scenes' text passed as `previous_text` / `next_text` for consistent prosody.
* `build/timing.json` = scenes `{start,end,speech_start,speech_end}`, `cues`, `captions` (sentence-level, from the alignment),
  `duration`, `mode` (`elevenlabs` | `estimate`).
* `--estimate` fakes timing from text length (14.5 chars/s + pauses) and writes no audio – for layout work only.
  Estimated cue times drift against the real voice; always re-check after the real narration.
* Pronunciation: spell out numbers, abbreviations, brand names the way they should sound; check by ear.

## Eleven v3 performance tags (`model: eleven_v3`)
Put directions in curly braces; they are sent to the API as `[tag]`, never shown in captions and never counted as cues:
```
{curious} Ever wondered why...? [ana] {whispers} Plopp... Plopp... {laughs} Classic! {dramatic} And then... silence.
```
Useful tags: `{excited}` `{curious}` `{sarcastic}` `{whispers}` `{laughs}` `{sighs}` `{dramatic}` `{confident}` `{warmly}`.
Use them sparingly (every 1–3 sentences), write short sentences, use `...` for beats. Recommended: `stability: 0.0` (creative) or `0.5`
(natural). v3 ignores `style`/`speed` partly and rejects `previous_text`/`next_text` (handled automatically).
