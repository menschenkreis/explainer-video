"""browser.py – launch a headless Chromium for shot.py / render_mp4.py.

Order: $EV_CHROME (path to a Chrome/Chromium binary) → installed Google Chrome → playwright's bundled chromium
→ a system chromium found on PATH. Lets the same code run on macOS, Linux, WSL and CI without config."""
import os, shutil


def launch(p):
    exe = os.environ.get("EV_CHROME")
    if exe:
        return p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    errors = []
    for kw in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            errors.append(str(e).splitlines()[0])
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return p.chromium.launch(executable_path=path, args=["--no-sandbox"])
    raise SystemExit("No Chrome/Chromium found. Install Google Chrome, run `ev setup`, or set EV_CHROME=/path/to/chrome.\n  " + "\n  ".join(errors))
