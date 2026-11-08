#!/usr/bin/env python3
"""new_project.py <dir> "<Title>"  – scaffold script.md + a sample scene so the first build works immediately."""
import sys
from pathlib import Path

d = Path(sys.argv[1]); title = sys.argv[2] if len(sys.argv) > 2 else "Explainer"
(d / "scenes").mkdir(parents=True, exist_ok=True); (d / "build").mkdir(exist_ok=True)
(d / "script.md").write_text(f"""---
title: {title}
lang: de
model: eleven_multilingual_v2
# voice_id: <ElevenLabs voice id – see narrate.py --list-voices>
lead: 0.7
gap: 0.7
tail: 2.0
---
> Quelle: <Buch, Kapitel, Seiten>

## intro | Einstieg
Willkommen. [titel] Heute geht es um {title}. [punkte] Drei Punkte stehen im Mittelpunkt.
""", encoding="utf-8")
(d / "scenes" / "01-intro.html").write_text("""<section class="scene" data-scene="intro" data-part="Teil 1">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">Kapitel</span>
    <h2 data-at="titel" data-fx="rise">Titel der Szene</h2>
  </div>
  <div class="body">
    <div class="abs row" style="left:0;top:40px;gap:24px" data-at="punkte" data-fx="rise">
      <div class="card ca" style="width:540px;height:260px"><h3>Punkt 1</h3><p>Kurzer Satz.</p></div>
      <div class="card cb" style="width:540px;height:260px" data-at="punkte+1.5" data-fx="rise"><h3>Punkt 2</h3><p>Kurzer Satz.</p></div>
      <div class="card cc" style="width:540px;height:260px" data-at="punkte+3" data-fx="rise"><h3>Punkt 3</h3><p>Kurzer Satz.</p></div>
    </div>
  </div>
</section>
""", encoding="utf-8")
print(f"created {d}/ – next: python3 narrate.py {d}/script.md --estimate --out {d} && python3 build.py {d}")
