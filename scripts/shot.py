#!/usr/bin/env python3
"""shot.py – screenshot frames of the built video (to verify visuals + sync without watching it).

  shot.py index.html --at 12 40.5          # specific times (s)
  shot.py index.html --scene elemente      # one frame ~1s after every cue + the final state of the scene
  shot.py index.html --all-scenes          # final state of every scene (overview)
Add --sheet to also tile everything into one contact-sheet PNG (needs ffmpeg).
Needs the venv from setup.sh (playwright) and Chrome/Chromium (see browser.py; EV_CHROME overrides).
"""
import argparse, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser import launch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--at", nargs="*", type=float, default=[])
    ap.add_argument("--scene", action="append", default=[])
    ap.add_argument("--all-scenes", action="store_true")
    ap.add_argument("--after", type=float, default=1.1, help="seconds after each cue to sample (default 1.1)")
    ap.add_argument("--out", default="build/shots")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--captions", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    scale = a.width / 1920
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=scale)
        msgs = []
        pg.on("console", lambda m: msgs.append(m.text) if m.type in ("warning", "error") else None)
        pg.on("pageerror", lambda e: msgs.append("PAGEERROR " + str(e)))
        pg.goto(Path(a.html).resolve().as_uri() + "?export=1" + ("" if a.captions else "&nocc=1"))
        pg.wait_for_function("window.__ready === true")
        if not a.captions:
            pg.evaluate("document.body.classList.add('nocc')")
        scenes, cues = pg.evaluate("[window.__scenes, window.__cues]")
        jobs = [(f"t{t:07.2f}".replace(".", "_"), t) for t in a.at]
        sel = list(scenes) if a.all_scenes else a.scene
        for sid in sel:
            sc = scenes[sid]
            if a.all_scenes:
                jobs.append((f"{sid}__end", sc["end"] - 0.6))
            else:
                for k, v in sorted(cues.items(), key=lambda kv: kv[1]):
                    if k.startswith(sid + "."):
                        jobs.append((f"{sid}__{k.split('.',1)[1]}", min(v + a.after, sc["end"] - 0.1)))
                jobs.append((f"{sid}__end", sc["end"] - 0.6))
        files = []
        for name, t in jobs:
            pg.evaluate(f"window.__seek({t})")
            f = out / f"{name}.png"; pg.screenshot(path=str(f)); files.append(f)
            print(f"{t:8.2f}s  {f}")
        missing = pg.evaluate("window.__missing")
        b.close()
    if missing: print("MISSING CUES:", missing)
    for m in dict.fromkeys(msgs): print("console:", m)
    if a.sheet and files:
        cols = 3 if len(files) > 4 else 2
        rows = [files[i:i + cols] for i in range(0, len(files), cols)]
        rowfiles = []
        for ri, r in enumerate(rows):
            rf = out / f"_row{ri}.png"
            cmd = ["ffmpeg", "-y", "-loglevel", "error"]
            for f in r: cmd += ["-i", str(f)]
            filt = "".join(f"[{i}:v]scale=640:-1[s{i}];" for i in range(len(r)))
            filt += "".join(f"[s{i}]" for i in range(len(r))) + (f"hstack=inputs={len(r)}" if len(r) > 1 else "null")
            subprocess.run(cmd + ["-filter_complex", filt, str(rf)], check=True); rowfiles.append(rf)
        sheet = out / "_sheet.png"
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for f in rowfiles: cmd += ["-i", str(f)]
        w = f"[{len(rowfiles)-1}:v]" ;
        filt = "".join(f"[{i}:v]pad=1920:ih[p{i}];" for i in range(len(rowfiles))) + "".join(f"[p{i}]" for i in range(len(rowfiles))) + (f"vstack=inputs={len(rowfiles)}" if len(rowfiles) > 1 else "null")
        subprocess.run(cmd + ["-filter_complex", filt, str(sheet)], check=True)
        print("sheet:", sheet)


if __name__ == "__main__":
    main()
