#!/usr/bin/env python3
"""ev – one command for the whole explainer-video pipeline.

  ev doctor                       check python / ffmpeg / Chrome / ElevenLabs key
  ev setup                        one-time install of the helper venv (pymupdf, playwright)
  ev key                          save your ElevenLabs key (hidden prompt, never echoed)
  ev voices                       list voices of your ElevenLabs account
  ev profile <dir>                learntype brainstorm: how do YOU learn, which analogies click? (writes learner-profile.json)
  ev ingest <files|folders…> [--out DIR]   drop in your material (pdf, docx, pptx, md, txt, html) → page-marked text + inventory
  ev plan <curriculum.json> [--scaffold]   validate the personalised curriculum, show the time budget, create one project per video
  ev calendar add <ics-url>       save your study-calendar feed privately (the URL contains a secret token)
  ev calendar fetch|blocks <dir>  download the feed / group it into study blocks (what is taught when, links to scan)
  ev new <dir> "Title" [--lang en]   scaffold a single project
  ev extract <pdf> --pages 10-30  pull chapter text out of a PDF (-o out.txt)
  ev preview <dir>                estimate timing + build + open in browser (no credits)
  ev narrate <dir> [--dry-run] [--only id,id]   ElevenLabs narration (cached per scene)
  ev build <dir>                  assemble <dir>/index.html
  ev shots <dir> [--all-scenes | --scene id] [--sheet]    screenshots to check layout / sync
  ev mp4 <dir> [--captions] [--start s --end s]            export video.mp4 (adds the ⬇ MP4 button)
  ev all <dir>                    narrate + build + mp4 + build
  ev site <site.json>             build the free static study website

Everything runs inside the project directory, so relative paths just work.
"""
import os, subprocess, sys, shutil, getpass, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
VENV = Path(os.environ.get("EV_VENV", Path.home() / ".local/share/explainer-video/venv"))
VPY = VENV / "bin" / "python"
ENV_FILE = Path.home() / ".config/explainer-video/.env"


def py(script, args, cwd=None, venv=False):
    exe = str(VPY) if venv and VPY.exists() else sys.executable
    if venv and not VPY.exists():
        sys.exit("The helper venv is missing – run:  ev setup")
    return subprocess.call([exe, str(SCRIPTS / script), *args], cwd=cwd)


def key_status():
    v = os.environ.get("ELEVENLABS_API_KEY", "")
    src = "environment"
    for p in (Path(".env"), ENV_FILE):
        if not v and p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    v = line.split("=", 1)[1].strip(); src = str(p)
    return (len(v) > 0), src


def doctor():
    ok = True
    def row(good, name, hint=""):
        nonlocal ok
        print(("  ✓ " if good else "  ✗ ") + name + ("" if good else f"   → {hint}"))
        ok = ok and good
    print("ev doctor")
    row(sys.version_info >= (3, 9), f"python {sys.version.split()[0]}", "needs Python ≥ 3.9")
    ff_hint = {"darwin": "brew install ffmpeg"}.get(sys.platform, "Debian/Ubuntu: sudo apt install ffmpeg · Fedora: dnf · Arch: pacman · Windows: use WSL")
    row(bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")), "ffmpeg + ffprobe", ff_hint)
    chrome = [p for p in (os.environ.get("EV_CHROME", ""), "/Applications/Google Chrome.app", "/Applications/Chromium.app") if p and Path(p).exists()]
    chrome += [w for w in map(shutil.which, ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")) if w]
    pw = any((Path.home() / d).is_dir() and any((Path.home() / d).glob("chromium*")) for d in ("Library/Caches/ms-playwright", ".cache/ms-playwright"))
    row(bool(chrome) or pw, "Chrome/Chromium (for screenshots + MP4 export)", f"install Google Chrome, set EV_CHROME=/path/to/chrome, or run: {VENV}/bin/playwright install chromium")
    row(VPY.exists(), "helper venv (pymupdf, playwright)", "run: ev setup")
    has_key, src = key_status()
    row(has_key, f"ElevenLabs key ({src})" if has_key else "ElevenLabs key", "run: ev key   (needed only for real narration; previews work without)")
    on_path = shutil.which("ev")
    print(("  ✓ " if on_path else "  • ") + ("`ev` on PATH" if on_path else "`ev` not on PATH – call it by full path, or add its folder (e.g. ~/.local/bin) to PATH; install.sh can do it for you (asks first)"))
    print("\nAll good." if ok else "\nFix the ✗ items above, then run ev doctor again.")
    return 0 if ok else 1


def save_key():
    k = getpass.getpass("ElevenLabs API key (input hidden): ").strip()
    if not k:
        sys.exit("no key entered")
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(f"ELEVENLABS_API_KEY={k}\n"); ENV_FILE.chmod(0o600)
    print(f"saved to {ENV_FILE} (permissions 600). The key needs the 'Text to Speech' permission (and 'Voices: Read' for ev voices).")


def need_dir(a):
    if len(a) < 1:
        sys.exit("usage: ev <command> <project-dir> …")
    d = Path(a[0])
    if not d.is_dir():
        sys.exit(f"{d} is not a directory (create one with: ev new {d} \"Title\")")
    return d.resolve(), a[1:]


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    c, a = a[0], a[1:]
    if c == "doctor": return doctor()
    if c == "setup": return subprocess.call(["bash", str(SCRIPTS / "setup.sh")])
    if c == "key": return save_key()
    if c == "voices": return py("narrate.py", ["--list-voices"])
    if c == "new": return py("new_project.py", a)
    if c == "profile": return py("profile.py", a)
    if c == "calendar":
        if not a or a[0] not in ("add", "fetch", "blocks", "file"): sys.exit("usage: ev calendar add <url> | fetch <dir> | blocks <dir> [--days N --past N --gap D --refresh] | file <x.ics> <dir>")
        sub, rest = a[0], a[1:]
        if sub == "add": return py("ical.py", ["add", *rest])
        if sub == "file": return py("ical.py", ["file", rest[0], "--out", rest[1] if len(rest) > 1 else ".", *rest[2:]])
        return py("ical.py", [sub, "--out", rest[0] if rest and not rest[0].startswith("-") else ".", *(rest[1:] if rest and not rest[0].startswith("-") else rest)])
    if c == "ingest": return py("ingest.py", a, venv=True)
    if c == "plan": return py("plan.py", a)
    if c == "extract": return py("extract_chapter.py", a, venv=True)
    if c == "site": return py("site_build.py", a)
    d, rest = need_dir(a)
    if c == "narrate": return py("narrate.py", ["script.md", *rest], cwd=d)
    if c == "build": return py("build.py", ["."], cwd=d)
    if c == "shots": return py("shot.py", ["index.html", *rest], cwd=d, venv=True)
    if c == "mp4": return py("render_mp4.py", ["index.html", "-o", "video.mp4", *rest], cwd=d, venv=True)
    if c == "preview":
        for step in (lambda: py("narrate.py", ["script.md", "--estimate"], cwd=d), lambda: py("build.py", ["."], cwd=d)):
            if step(): return 1
        idx = d / "index.html"
        if os.environ.get("EV_NO_OPEN") or not webbrowser.open(idx.as_uri()):
            print(f"open in your browser: {idx}")
        return 0
    if c == "all":
        for step in (lambda: py("narrate.py", ["script.md", *rest], cwd=d), lambda: py("build.py", ["."], cwd=d),
                     lambda: py("render_mp4.py", ["index.html", "-o", "video.mp4", "--captions", "--workers", "4"], cwd=d, venv=True),
                     lambda: py("build.py", ["."], cwd=d)):
            if step(): return 1
        return 0
    sys.exit(f"unknown command '{c}' – see: ev --help")


if __name__ == "__main__":
    sys.exit(main())
