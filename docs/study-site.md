# Free study website (`ev site`)

Builds a plain static website from your video projects: overview → per-video study page → flashcards.
No framework, no build step, no cookies, no external requests – GDPR-friendly and fast.

## site.json
```json
{
  "title": "Learn Optics", "subtitle": "Explainer videos, mnemonics and self-tests", "lang": "en",
  "notice": "Own summary with own examples. Sources: …",
  "courses": [{
    "id": "optics", "title": "Light and colour", "source": "optional source line",
    "videos": [{
      "slug": "rainbow", "title": "How a rainbow forms", "dir": "../videos/rainbow",
      "summary": "One-line description shown on the cards.",
      "mnemonics": ["Roy G. Biv"],
      "quiz": [{"q": "Which colour bends the most?", "a": "Violet."}]
    }]
  }]
}
```
`dir` points at a built project (`index.html`, `narration.mp3`, optional `video.mp4`, `build/timing.json`); paths are relative to `site.json`.
`lang` supports `de` and `en` (strings live at the top of `scripts/site_build.py`).

## Interactive drills (`exercises`) and `links`
Add `"exercises": [...]` to a video (from `curriculum.json` they are copied by `ev plan --scaffold`). They appear on the video page and on
a combined **Übungen / Exercises** page. Everything is computed in the browser; nothing is stored or sent.

| type | fields | what the learner does |
|---|---|---|
| `prefmatrix` | `criteria` [names], optional `answers` {"i-j": winner index}, `solution` {name: weight %}, `tolerance` (1), `plus_one` (add 1 to every count so nothing ends at 0 %), `total` (100) | picks the more important criterion for every pair → counts, rank, weights; **Prüfen** compares with `solution` |
| `nwa` | `criteria` [{name, weight}], `variants` [names], `max` (10), optional `musts` [text], `must_ok` [[bool per must] per variant], `scores` [[per criterion] per variant] | ticks must-haves (a variant failing one is excluded), enters points → utility = Σ weight × points, best variant highlighted |
| `conflict` | `goals` [names], optional `solution` {"i-j": "+" \| "0" \| "-"} | rates every goal pair supporting / neutral / conflicting → list of conflicts, check against solution |
| `steps` | `steps` [{q, a}], optional `intro` | worked example: next step / show answer, one at a time |

Every type takes `title` and an optional `task` (one-line instruction). Indices in `"i-j"` keys are 0-based with i < j.
`"links": [{"title": "SE-Studio", "href": "…"}]` adds buttons to other tools (an app, the course page) – only link what the learner may share.

## What a visitor gets
* overview of courses and videos with lengths
* per video: the player (in-page), **⬇ MP4** and MP3 download, clickable chapters, mnemonics, self-test questions (reveal on click),
  full transcript, “mark as learned” (stored only in the visitor’s browser)
* a flashcard page with every mnemonic and self-test question (flip, shuffle, filter)
* an exercises page with every interactive drill (when any video has `exercises`)

## Hosting for free
* **GitHub Pages:** push the `site/` folder (or the whole repo) and enable Pages → Settings → Pages.
* **Cloudflare Pages / Netlify:** drag-and-drop the `site/` folder.
* **Your own web space (e.g. Plesk):** upload `site/` into a sub-folder such as `/learn/`.
All paths are relative, so it works under any sub-path. MP4s are the big files (~3–4 MB per minute); consider linking
large videos from a CDN if your host has a size limit.
