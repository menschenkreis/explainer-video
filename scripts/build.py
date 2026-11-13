#!/usr/bin/env python3
"""build.py – assemble index.html from engine + scenes/*.html + build/timing.json   (stdlib only)

Run `narrate.py` (or `narrate.py --estimate`) first so build/timing.json exists.
Validates that:
  * every ## scene in script.md has a scenes/*.html fragment with a matching data-scene
  * every cue used in data-at / data-out exists in the script as a [marker]
  * every [marker] in the script is used by at least one element (warning)
"""
import argparse, json, re, sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "engine"
AT = re.compile(r'data-(?:at|out)="([^"]+)"')
SCENE = re.compile(r'data-scene="([^"]+)"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    a = ap.parse_args()
    root = Path(a.project)
    timing_p = root / "build" / "timing.json"
    if not timing_p.exists():
        sys.exit("build/timing.json missing – run narrate.py (add --estimate to preview without audio) first")
    timing = json.loads(timing_p.read_text(encoding="utf-8"))

    frags = sorted((root / "scenes").glob("*.html"))
    if not frags:
        sys.exit("no scenes/*.html fragments found")
    html_scenes, seen_ids, used, problems = [], [], set(), 0
    for f in frags:
        txt = f.read_text(encoding="utf-8")
        m = SCENE.search(txt)
        if not m:
            print(f"ERROR {f.name}: no data-scene attribute"); problems += 1; continue
        sid = m.group(1); seen_ids.append(sid)
        if sid not in timing["scenes"]:
            print(f"ERROR {f.name}: scene '{sid}' is not in script.md"); problems += 1
        for spec in AT.findall(txt):
            mm = re.match(r"\s*(@?[\w.]+)", spec)
            base = mm.group(1) if mm else ""
            if base.startswith("@"):
                continue
            key = base if "." in base else f"{sid}.{base}"
            used.add(key)
            if key not in timing["cues"]:
                print(f"ERROR {f.name}: cue '{key}' used in markup but not in script.md"); problems += 1
        html_scenes.append(txt)
    for sid in timing["order"]:
        if sid not in seen_ids:
            print(f"ERROR script scene '{sid}' has no scenes/*.html fragment"); problems += 1
    alltxt = "\n".join(html_scenes)
    for key in timing["cues"]:
        sid, _, name = key.partition(".")
        if key not in used and not re.search(r"""['"]""" + re.escape(name) + r"""(?=[+\-'"])""", alltxt):
            print(f"warning: cue '{key}' is in the script but nothing uses it")

    tpl = (ENGINE / "player.html").read_text(encoding="utf-8")
    css = (ENGINE / "theme.css").read_text(encoding="utf-8")
    proj_css = (root / "theme.css").read_text(encoding="utf-8") if (root / "theme.css").exists() else ""
    js = (ENGINE / "engine.js").read_text(encoding="utf-8")
    audio_attr = f'src="{timing["audio"]}"' if timing.get("audio") else ""
    # "download as MP4" button: shown when video.mp4 (from render_mp4.py) sits next to index.html
    dl = ""
    if (root / "video.mp4").exists():
        fname = re.sub(r"[^A-Za-z0-9._-]+", "_", (timing.get("title") or "video")).strip("_")[:80] + ".mp4"
        dl = f'<a id="dl" href="video.mp4" download="{fname}" title="Download MP4">⬇ MP4</a>'
    out = (tpl.replace("{{LANG}}", timing.get("lang", "en")).replace("{{TITLE}}", timing.get("title") or "Explainer")
           .replace("{{THEME}}", css).replace("{{PROJECT_CSS}}", proj_css)
           .replace("{{SCENES}}", "\n".join(html_scenes)).replace("{{AUDIO_ATTR}}", audio_attr)
           .replace("{{START}}", {"de": "▶ Video starten", "en": "▶ Start video", "fr": "▶ Lancer la vidéo", "es": "▶ Iniciar vídeo", "it": "▶ Avvia video"}.get(timing.get("lang", "en")[:2], "▶ Start"))
           .replace("{{DL_BTN}}", dl).replace("{{TIMING_JSON}}", json.dumps(timing, ensure_ascii=False)).replace("{{ENGINE}}", js))
    (root / "index.html").write_text(out, encoding="utf-8")
    print(f'index.html written ({len(out)//1024} KB, {len(frags)} scenes, mode={timing["mode"]}, {timing["duration"]/60:.1f} min)')
    if problems:
        sys.exit(f"{problems} problem(s) – fix and rebuild")


if __name__ == "__main__":
    main()
