# Scene DSL (`scripts/kit.py`) – one Python file per video

Write narration and picture side by side; `write()` produces `script.md` + `scenes/NN-id.html` and checks every cue.
```python
# <course>/_tools/v2.py          (writes <course>/<slug>/ – or set root=…, or $EV_COURSE_DIR)
from kit import *
S = []
S.append(dict(id="grenze", menu="Systemgrenze", part="System", kick="Kap. 1.1", title="Wo hört das System auf?",
  say="""{curious} Wo ziehst du die Grenze? [haut] Beim Körper ist es die Haut. [regel] Die Regel: innen klebt's mehr.""",
  body= node("g_body", 200, 80, 400, 300, "Körper", "c", "haut", ghost=True)
      + merk("Innen klebt's mehr", "Übergewicht der inneren Bindung, S. 30", cue="regel")
      + src("schematisch nach Abb. 1.2")))
write("b1-v2-system", dict(title="Video 2: Was ist ein System?", voice_id="…"), S,
      sources="Quelle: Buch Teil I (Seiten in den Szenen). Analogien und Fallbeispiel sind eigene Ergänzungen.")
```
`ev kit <course>/_tools/v2.py --shots` → writes the project, estimates timing, builds `index.html`, screenshot sheet in `build/shots/_sheet.png`
(`Read` it). A project-local `kit.py` next to the file wins over the skill's – copy the skill's one in when you want to freeze it.

| helper | use |
|---|---|
| `box(x,y,w,h,html,k,cue,fx)` · `txt(x,y,w,html,fs,cue)` · `chip(label,k)` · `h3` · `pts([(cue,html)])` | cards, free text, tags, bullet lists |
| `node(id,…)` · `edge(a,b,k,cue,arrow,curve,dash)` · `graph(x,y,w,h,nodes,edges)` · `bub(…)` · `lab(…)` | networks, bubble charts (ids unique per video!) |
| `table(x,y,w,cols,rows)` | rows appear one by one (`rows=[(cue,[cells],colour)]`) – matrices, Nutzwert tables |
| `merk(phrase,sub,cue)` | mnemonic banner |
| `task(x,y,w,h,title,html)` · `pause(x,y,w,cue)` · `bar(…)` | exam-style drill: task card + "pause and solve" bar |
| `ncard(i,…)` · `recap4(cards,next_html,foot)` · `roadmap(n,names)` | numbered cards, recap scene, course strip (video n lit) |
| `svg(x,y,w,h,inner)` · `emoji(x,y,ch)` · `src(text)` | free SVG, big emoji, source line |

Colours `k`: `a b c d e ok`. Stage body 1728 × 780 px; keep content above y ≈ 740. `EV_LANG=en` switches the default labels.
`write()` warns about cues used but not spoken (error), spoken but unused, cues spoken twice, scenes > 900 characters.
