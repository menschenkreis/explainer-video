#!/usr/bin/env python3
"""render_mp4.py – export the coded video to an MP4 (frame-exact, narration muxed in).

  render_mp4.py index.html -o video.mp4 [--fps 30] [--width 1920] [--workers 4] [--captions]
  render_mp4.py index.html -o test.mp4 --start 60 --end 75        # render a short excerpt

How: headless Chrome loads index.html?export=1, window.__seek(t) draws each frame exactly,
frames are piped to ffmpeg; several workers render time-slices in parallel and the slices are
concatenated, then narration.mp3 is muxed.  Nothing is recorded in real time.
"""
import argparse, subprocess, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def render_slice(args):
    html, i0, i1, fps, width, captions, part = args
    from playwright.sync_api import sync_playwright
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                           "-vf", f"scale={width}:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(part)],
                          stdin=subprocess.PIPE)
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(Path(html).resolve().as_uri() + "?export=1")
        pg.wait_for_function("window.__ready === true")
        if not captions:
            pg.evaluate("document.body.classList.add('nocc')")
        for i in range(i0, i1):
            pg.evaluate(f"window.__seek({i / fps:.5f})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=93))
        b.close()
    ff.stdin.close(); ff.wait()
    return str(part)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html"); ap.add_argument("-o", "--out", default="video.mp4")
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--captions", action="store_true", help="burn subtitles in")
    ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float, default=None)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            b = p.chromium.launch()
        pg = b.new_page(); pg.goto(Path(a.html).resolve().as_uri() + "?export=1"); pg.wait_for_function("window.__ready === true")
        dur = pg.evaluate("window.__duration"); b.close()
    end = min(a.end or dur, dur)
    f0, f1 = int(a.start * a.fps), int(end * a.fps)
    n = max(1, min(a.workers, (f1 - f0) // (a.fps * 5) or 1))
    bounds = [f0 + (f1 - f0) * k // n for k in range(n + 1)]
    tmp = Path(tempfile.mkdtemp(prefix="evr_"))
    jobs = [(a.html, bounds[k], bounds[k + 1], a.fps, a.width, a.captions, tmp / f"part{k}.mp4") for k in range(n)]
    print(f"rendering {f1 - f0} frames ({(end - a.start):.1f}s @ {a.fps}fps) with {n} worker(s)…", flush=True)
    with ProcessPoolExecutor(n) as ex:
        parts = list(ex.map(render_slice, jobs))
    lst = tmp / "list.txt"; lst.write_text("".join(f"file '{x}'\n" for x in parts))
    cat = tmp / "video_only.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(cat)], check=True)
    audio = Path(a.html).resolve().parent / "narration.mp3"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(cat)]
    if audio.exists():
        cmd += ["-ss", str(a.start), "-t", str(end - a.start), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        print("note: no narration.mp3 – exporting silent video")
        cmd += ["-c:v", "copy"]
    subprocess.run(cmd + [a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
