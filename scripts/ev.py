#!/usr/bin/env python3
"""ev – one command for the whole explainer-video pipeline.

  ev doctor                       check python / ffmpeg / Chrome / ElevenLabs key
  ev setup                        one-time install of the helper venv (pymupdf, playwright)
  ev key                          save your ElevenLabs key (hidden prompt, never echoed)
  ev voices                       list voices of your ElevenLabs account
  ev profile <dir>                learntype brainstorm: how do YOU learn, which analogies click? (writes learner-profile.json)
  ev ingest <files|folders…> [--out DIR]   drop in your material (pdf, docx, pptx, md, txt, html) → page-marked text + inventory
  ev plan <curriculum.json> [--scaffold]   validate the personalised curriculum, show the time budget, create one project per video
  ev new <dir> "Title"            scaffold a single project
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
import os, subprocess, sys, shutil, getpass
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
    row(bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")), "ffmpeg + ffprobe", "macOS: brew install ffmpeg · Debian/Ubuntu: apt install ffmpeg")
    chrome = [p for p in ("/Applications/Google Chrome.app", "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser") if Path(p).exists()]
    row(bool(chrome) or (VENV / "bin").exists(), "Chrome/Chromium (for screenshots + MP4 export)", "install Google Chrome, or after 'ev setup' run: playwright install chromium")
    row(VPY.exists(), "helper venv (pymupdf, playwright)", "run: ev setup")
    has_key, src = key_status()
    row(has_key, f"ElevenLabs key ({src})" if has_key else "ElevenLabs key", "run: ev key   (needed only for real narration; previews work without)")
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
        subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", str(idx)])
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
