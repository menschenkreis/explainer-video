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

## What a visitor gets
* overview of courses and videos with lengths
* per video: the player (in-page), **⬇ MP4** and MP3 download, clickable chapters, mnemonics, self-test questions (reveal on click),
  full transcript, “mark as learned” (stored only in the visitor’s browser)
* a flashcard page with every mnemonic and self-test question (flip, shuffle, filter)

## Hosting for free
* **GitHub Pages:** push the `site/` folder (or the whole repo) and enable Pages → Settings → Pages.
* **Cloudflare Pages / Netlify:** drag-and-drop the `site/` folder.
* **Your own web space (e.g. Plesk):** upload `site/` into a sub-folder such as `/learn/`.
All paths are relative, so it works under any sub-path. MP4s are the big files (~3–4 MB per minute); consider linking
large videos from a CDN if your host has a size limit.
