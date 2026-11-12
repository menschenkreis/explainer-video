#!/usr/bin/env python3
"""kit.py – scene DSL: write a whole video as ONE Python file, narration and picture side by side.

    # course/_tools/v1.py
    from kit import *
    S = [dict(id="hook", menu="Einstieg", part="Einstieg", kick="Video 1", title="Die Landkarte",
              say="{curious} Fünfundvierzig Prozent. [score] Das war die Lernkontrolle.",
              body=box(0, 10, 520, 270, "<b>45 %</b>", "d", "score"))]
    write("v1-landkarte", dict(title="Video 1: Die Landkarte", voice_id="…"), S, sources="Quelle: Buch, Kap. 1 (Seiten in den Szenen).")

Run it with `ev kit course/_tools/v1.py [--shots]` (writes script.md + scenes/, then estimate → build → screenshot sheet),
or `python3 v1.py` with this folder on PYTHONPATH. A project-local kit.py next to the video file wins over this one.

Output folder: write(slug, …, root=…) → <root>/<slug>. Default root: $EV_COURSE_DIR, else the parent of the folder that
holds the video file (course/_tools/v1.py → course/<slug>).

Stage body = 1728 × 780 px; keep content above y ≈ 740 (captions sit below). Colours k: a b c d e ok (theme tokens).
Every helper takes cue=…, fx=… (engine effects: rise pop fade left draw growx hl hlfill …), and most take out=… (cue to leave).
"""
import os, pathlib, re, shutil, subprocess, sys

K = {"a": "ca", "b": "cb", "c": "cc", "d": "cd", "e": "ce", "ok": "cok", "": ""}
CPM = {"de": 780, "en": 900, "fr": 850, "es": 900, "it": 850}     # narrated characters per minute (same table as plan.py)
LABELS = {"de": dict(merk="Merk dir", task="Aufgabe", pause="⏸ Pause drücken und selbst lösen", video="Video"),
          "en": dict(merk="Remember", task="Task", pause="⏸ Pause now and solve it yourself", video="Video")}
LANG = os.environ.get("EV_LANG", "de")


def L(key):
    return LABELS.get(LANG, LABELS["en"])[key]


def at(cue=None, fx=None, dur=None, out=None):
    s = ""
    if cue:
        s += f' data-at="{cue}"'
        if fx:
            s += f' data-fx="{fx}"'
    if dur:
        s += f' data-dur="{dur}"'
    if out:
        s += f' data-out="{out}"'
    return s


def scene(sid, part, kick, title, body):
    return f'''<section class="scene" data-scene="{sid}" data-part="{part}">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">{kick}</span>
    <h2 data-at="@start+0.3" data-fx="rise">{title}</h2>
  </div>
  <div class="body">
{body}
  </div>
</section>
'''


# ------------------------------------------------------------------ primitives
def box(x, y, w, h, inner, k="", cue=None, fx="rise", style="", cls="card", out=None, dur=None):
    hh = f"height:{h}px;" if h else ""
    return (f'<div class="{cls} {K.get(k, k)} abs" style="left:{x}px;top:{y}px;width:{w}px;{hh}{style}"'
            f'{at(cue, fx, dur, out)}>{inner}</div>\n')


def txt(x, y, w, inner, fs=30, cue=None, fx="fade", color=None, weight=None, align=None, style="", out=None, lh=1.25):
    st = f"left:{x}px;top:{y}px;width:{w}px;font-size:{fs}px;line-height:{lh};"
    if color:
        st += f"color:var(--{color});"
    if weight:
        st += f"font-weight:{weight};"
    if align:
        st += f"text-align:{align};"
    return f'<div class="abs" style="{st}{style}"{at(cue, fx, None, out)}>{inner}</div>\n'


def chip(label, k="a", fill=True, fs=22, style=""):
    return f'<span class="chip {K[k]}{" fill" if fill else ""}" style="font-size:{fs}px;padding:3px 14px;{style}">{label}</span>'


def h3(label, fs=34, color=None, style=""):
    c = f"color:var(--{color});" if color else ""
    return f'<h3 style="font-size:{fs}px;{c}{style}">{label}</h3>'


def pts(items, k="a", fs=28, gap=12, fx="rise"):
    """bullet list; items = [(cue_or_None, html)]"""
    lis = "".join(f'<li style="font-size:{fs}px;margin-bottom:{gap}px"{at(c, fx)}>{t}</li>' for c, t in items)
    return f'<ul class="pts" style="--k:var(--{k})">{lis}</ul>'


def node(nid, x, y, w, h, label, k="c", cue=None, fx="pop", fill=False, ghost=False, fs=28, style="", out=None):
    """graph node; nid must be unique across the WHOLE video (prefix it with the scene id)"""
    cls = "node " + K[k] + (" fill" if fill else "") + (" ghost" if ghost else "")
    return (f'<div class="{cls}" id="{nid}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-size:{fs}px;{style}"'
            f'{at(cue, fx, None, out)}>{label}</div>\n')


def edge(a, b, k="", cue=None, arrow=None, curve=None, dash=False, pad=None, dur=None, out=None):
    """auto-routed arrow between two node ids (arrow: 'end'|'both'|'none', curve: bend in px)"""
    s = f'<g class="edge {K[k]}{" dash" if dash else ""}" data-edge="{a}>{b}"'
    if arrow:
        s += f' data-arrow="{arrow}"'
    if curve is not None:
        s += f' data-curve="{curve}"'
    if pad is not None:
        s += f' data-pad="{pad}"'
    return s + at(cue, "edge", dur, out) + "></g>\n"


def graph(x, y, w, h, nodes, edges="", extra=""):
    return (f'<div class="graph abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">\n'
            f'<svg class="edges">{edges}</svg>\n{nodes}{extra}</div>\n')


def svg(x, y, w, h, inner, style=""):
    return (f'<svg class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:visible;{style}" '
            f'viewBox="0 0 {w} {h}">{inner}</svg>\n')


def emoji(x, y, ch, size=96, cue=None, fx="pop", out=None):
    return f'<div class="abs" style="left:{x}px;top:{y}px;font-size:{size}px;line-height:1"{at(cue, fx, None, out)}>{ch}</div>\n'


def src(text, y=748, x=0, w=1728, cue="@start+1"):
    """small source line (book page, 'schematisch nach Abb. x.y')"""
    return txt(x, y, w, text, 20, cue, "fade", "mute")


def bar(x, y, w, k="a", cue=None, dur=3, h=10):
    """thin bar that fills over `dur` seconds (e.g. 'pause now' moments)"""
    return (f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:9px;background:var(--line)"{at(cue, "fade")}></div>\n'
            f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:9px;background:var(--{k})"{at(cue, "growx", dur)}></div>\n')


# ------------------------------------------------------------------ composites
def merk(phrase, sub=None, cue="merk", y=600, h=None, label=None, k="a", fs=46):
    """full-width mnemonic banner"""
    h = h or (150 if sub else 112)
    s = f'<div class="mute" style="font-size:26px;margin-top:4px">{sub}</div>' if sub else ""
    inner = (f'<div style="display:flex;align-items:center;gap:22px">{chip(label or L("merk"), k)}'
             f'<div style="font-size:{fs}px;font-weight:800;line-height:1.12;color:var(--{k})">{phrase}</div></div>{s}')
    return box(0, y, 1728, h, inner, k, cue, "rise", "padding:20px 30px;")


def roadmap(n, names, cue="road", y=640, label=None, done_k="b", todo_k="e"):
    """the course's videos as a strip, video n (1-based) lit; names = short titles (≤ 6 fit)"""
    out, g = "", 19.5
    w = (1728 - g * (len(names) - 1)) / len(names)
    for i, nm in enumerate(names):
        on = (i + 1 == n)
        k = "a" if on else (done_k if i + 1 < n else todo_k)
        inner = (f'<div style="font-size:22px;font-weight:700;color:var(--{k})">{label or L("video")} {i+1}</div>'
                 f'<div style="font-size:24px;font-weight:700;line-height:1.1;margin-top:2px">{nm}</div>')
        out += box(round(i * (w + g)), y, round(w), 112, inner, k if on else "", f"{cue}+{0.12*i:.2f}", "rise",
                   "padding:12px 16px;" + ("" if on else "opacity:.5;"))
    return out


def ncard(i, x, y, w, h, col, head, sub, cue, fx="rise", hs=32, ss=25):
    """numbered card: big number/emoji + headline + sub line"""
    s = f'<div style="font-size:{ss}px;line-height:1.22;margin-top:5px">{sub}</div>' if sub else ""
    return box(x, y, w, h, f'<div style="display:flex;gap:18px;align-items:flex-start"><span style="font-size:{hs+26}px;font-weight:800;color:var(--{col});line-height:1">{i}</span>'
               f'<div><div style="font-size:{hs}px;font-weight:800;line-height:1.14;color:var(--{col})">{head}</div>{s}</div></div>', col, cue, fx, "padding:18px 24px;")


def bub(nid, x, y, w, h, label, k, cue, fill=False, fs=28):
    """bubble (rounded node) – bubble charts, Umsysteme"""
    return node(nid, x, y, w, h, label, k, cue, fill=fill, fs=fs, style="border-radius:999px;")


def lab(x, y, t, cue, col=None, w=220, fs=24):
    """small centred label (edge captions)"""
    return txt(x, y, w, t, fs, cue, "fade", col or "mute", 600, "center")


def task(x, y, w, h, title, inner, cue="task", label=None):
    """exam-style task card (drill)"""
    return box(x, y, w, h, f'{chip(label or L("task"), "a")}<div style="font-size:33px;font-weight:800;margin:10px 0 8px;line-height:1.15">{title}</div>{inner}', "a", cue, "left", "padding:20px 26px;")


def pause(x, y, w, cue="pause", text=None, dur=4):
    """'pause the video and solve it' prompt with a filling bar"""
    return txt(x, y, w, text or L("pause"), 30, cue, "pop", "a", 800, "center") + bar(x, y + 50, w, "a", cue, dur)


def recap4(cards, nxt, foot, cue_next="next"):
    """recap: cards = [(col, head, sub)] × 4 ; nxt = html for the 'next video' strip"""
    out = ""
    for i, (col, head, sub) in enumerate(cards):
        out += ncard(i + 1, (i % 2) * 876, (i // 2) * 194, 852, 170, col, head, sub, f"r{i+1}", hs=33, ss=26)
    out += box(0, 420, 1728, 120, nxt, "b", cue_next, "pop", "padding:26px 30px;font-size:34px;")
    out += txt(0, 580, 1728, foot, 26, f"{cue_next}+3", "fade", "mute", align="center")
    return out


def table(x, y, w, cols, rows, cue_prefix="t", fs=25, rowh=58, head_k="a"):
    """cols = [(label, width_px)], rows = [(cue, [cells], color_or_None)] – cells may contain html"""
    out = f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px">'
    out += '<div style="display:flex;border-bottom:3px solid var(--%s)">' % head_k + "".join(
        f'<div style="width:{cw}px;padding:8px 12px;font-size:{fs-3}px;font-weight:800;color:var(--{head_k});letter-spacing:.03em">{cl}</div>' for cl, cw in cols) + "</div>"
    for cue, cells, col in rows:
        bg = f"background:color-mix(in srgb,var(--{col}) 12%,transparent);" if col else ""
        out += f'<div style="display:flex;align-items:center;min-height:{rowh}px;border-bottom:1px solid var(--line);{bg}"{at(cue, "rise")}>' + "".join(
            f'<div style="width:{cols[j][1]}px;padding:6px 12px;font-size:{fs}px;line-height:1.2">{c}</div>' for j, c in enumerate(cells)) + "</div>"
    return out + "</div>\n"


# ------------------------------------------------------------------ writer
FRONT = {"lang": "de", "model": "eleven_v3", "stability": 0.5, "similarity": 0.8, "style": 0, "lead": 0.6, "gap": 0.5, "tail": 2.0}


def course_root():
    if os.environ.get("EV_COURSE_DIR"):
        return pathlib.Path(os.environ["EV_COURSE_DIR"]).resolve()
    main = getattr(sys.modules.get("__main__"), "__file__", None)
    return pathlib.Path(main).resolve().parent.parent if main else pathlib.Path.cwd()


def write(slug, meta, scenes, root=None, sources=None):
    """scenes = [dict(id, menu, part, kick, title, say, body)] → <root>/<slug>/script.md + scenes/NN-id.html.
    meta = script front matter (title, voice_id, model, lang, …; voice_id falls back to $ELEVENLABS_VOICE_ID).
    sources = one '> ' note line at the top of script.md (where the content comes from, what is your own addition)."""
    d = pathlib.Path(root).resolve() / slug if root else course_root() / slug
    sd = d / "scenes"
    if sd.exists():
        shutil.rmtree(sd)
    sd.mkdir(parents=True)
    fm = dict(FRONT)
    if os.environ.get("ELEVENLABS_VOICE_ID"):
        fm["voice_id"] = os.environ["ELEVENLABS_VOICE_ID"]
    fm.update(meta)
    fm.pop("note", None)
    out = "---\n" + "".join(f"{k}: {v}\n" for k, v in fm.items()) + "---\n\n"
    note = sources or meta.get("note")
    if note:
        out += "> " + " ".join(str(note).split()) + "\n\n"
    total, problems = 0, 0
    for i, s in enumerate(scenes, 1):
        say = " ".join(s["say"].split())
        spoken = re.sub(r"\[[A-Za-z0-9_]+\]|\{[^}]*\}", "", say)
        total += len(spoken)
        out += f"## {s['id']} | {s['menu']}\n{say}\n\n"
        (sd / f"{i:02d}-{s['id']}.html").write_text(scene(s["id"], s["part"], s["kick"], s["title"], s["body"]), encoding="utf-8")
        cues = re.findall(r"\[([A-Za-z0-9_]+)\]", say)
        dup = sorted({c for c in cues if cues.count(c) > 1})
        if dup:
            print(f"  !! {slug}/{s['id']}: cue(s) spoken twice: {dup}"); problems += 1
        used = set(re.findall(r'data-(?:at|out)="([A-Za-z0-9_]+)(?:[+-][0-9.]+)?"', s["body"]))
        miss = used - set(cues)
        if miss:
            print(f"  !! {slug}/{s['id']}: cue(s) used but not spoken: {sorted(miss)}"); problems += 1
        unused = set(cues) - used
        if unused:
            print(f"  .. {slug}/{s['id']}: spoken cue(s) without visual: {sorted(unused)}")
        if len(spoken) > 900:
            print(f"  .. {slug}/{s['id']}: long scene ({len(spoken)} chars, aim for 30–70 s)")
    (d / "script.md").write_text(out, encoding="utf-8")
    cpm = CPM.get(str(fm.get("lang", "de")), 800)
    print(f"{slug}: {len(scenes)} scenes, {total} chars ≈ {total / cpm:.1f} min  → {d}")
    rep = os.environ.get("EV_KIT_REPORT")
    if rep:
        with open(rep, "a", encoding="utf-8") as f:
            f.write(str(d) + "\n")
    return problems


# ------------------------------------------------------------------ ev kit <file.py> [--shots]
def _run(argv):
    import tempfile
    if not argv:
        sys.exit("usage: ev kit <video-file.py> [--shots]")
    f = pathlib.Path(argv[0]).resolve(); shots = "--shots" in argv
    here = pathlib.Path(__file__).resolve().parent
    venv_py = pathlib.Path(os.environ.get("EV_VENV", pathlib.Path.home() / ".local/share/explainer-video/venv")) / "bin/python"
    rep = tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False).name
    env = dict(os.environ, EV_KIT_REPORT=rep, PYTHONPATH=os.pathsep.join([str(f.parent), str(here), os.environ.get("PYTHONPATH", "")]))
    if subprocess.call([sys.executable, str(f)], cwd=f.parent, env=env):
        return 1
    dirs = [l.strip() for l in open(rep, encoding="utf-8") if l.strip()]
    os.unlink(rep)
    if not dirs:
        sys.exit("the file ran, but no project was written by this kit (a project-local kit.py does not report its folder) – "
                 "run: ev preview <video-dir>")
    for d in dict.fromkeys(dirs):
        print(f"\n▸ {d}")
        for cmd, py in ((["narrate.py", "script.md", "--estimate"], sys.executable), (["build.py", "."], sys.executable)):
            if subprocess.call([py, str(here / cmd[0]), *cmd[1:]], cwd=d):
                return 1
        if shots:
            shutil.rmtree(pathlib.Path(d) / "build/shots", ignore_errors=True)
            subprocess.call([str(venv_py) if venv_py.exists() else sys.executable, str(here / "shot.py"), "index.html", "--all-scenes", "--sheet"], cwd=d)
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        sys.exit(_run(sys.argv[2:]))
    print(__doc__)
