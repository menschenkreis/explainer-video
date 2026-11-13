#!/usr/bin/env python3
"""new_project.py <dir> "<Title>" [--lang en]  – scaffold script.md + a sample scene so the first build works immediately.

--lang is an ISO code (en, de, fr, …). It sets narration/caption language; the sample text is English – replace it anyway."""
import argparse
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("title", nargs="?", default="Explainer")
ap.add_argument("--lang", default="en"); a = ap.parse_args()
d = Path(a.dir); title = a.title
(d / "scenes").mkdir(parents=True, exist_ok=True); (d / "build").mkdir(exist_ok=True)
(d / "script.md").write_text(f"""---
title: {title}
lang: {a.lang}
model: eleven_multilingual_v2
# voice_id: <ElevenLabs voice id – see: ev voices>
lead: 0.7
gap: 0.7
tail: 2.0
---
> Source: <book, chapter, pages>

## intro | Introduction
Welcome. [title] Today we look at {title}. [points] Three points matter most.
""", encoding="utf-8")
(d / "scenes" / "01-intro.html").write_text("""<section class="scene" data-scene="intro" data-part="Part 1">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">Chapter</span>
    <h2 data-at="title" data-fx="rise">Scene title</h2>
  </div>
  <div class="body">
    <div class="abs row" style="left:0;top:40px;gap:24px" data-at="points" data-fx="rise">
      <div class="card ca" style="width:540px;height:260px"><h3>Point 1</h3><p>One short sentence.</p></div>
      <div class="card cb" style="width:540px;height:260px" data-at="points+1.5" data-fx="rise"><h3>Point 2</h3><p>One short sentence.</p></div>
      <div class="card cc" style="width:540px;height:260px" data-at="points+3" data-fx="rise"><h3>Point 3</h3><p>One short sentence.</p></div>
    </div>
  </div>
</section>
""", encoding="utf-8")
print(f"created {d}/ – next: ev preview {d}")
