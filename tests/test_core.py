"""Smoke tests: no network, no browser. Run:  python -m unittest discover -s tests -v   (needs ffmpeg)"""
import json, os, shutil, subprocess, sys, tempfile, threading, time, unittest
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SC = ROOT / "scripts"
sys.path.insert(0, str(SC))
import narrate  # noqa: E402


class Parsing(unittest.TestCase):
    def test_cues_and_audio_tags(self):
        text, marks, disp, dmap = narrate.strip_markers("Hallo. {excited} Das [cue] ist {laughs} cool!  Echt.")
        self.assertEqual(text, "Hallo. [excited] Das ist [laughs] cool! Echt.")
        self.assertEqual(disp, "Hallo. Das ist cool! Echt.")
        self.assertEqual(text[marks[0][1]:marks[0][1] + 3], "ist")
        self.assertEqual("".join(text[i] for i in dmap), disp)

    def test_plain_markers(self):
        text, marks, disp, _ = narrate.strip_markers("A [x] B  [y]C")
        self.assertEqual(text, "A B C"); self.assertEqual([m[0] for m in marks], ["x", "y"]); self.assertEqual(disp, text)


class Pipeline(unittest.TestCase):
    def run_py(self, script, *args, cwd=None, env=None):
        return subprocess.run([sys.executable, str(SC / script), *args], cwd=cwd, capture_output=True, text=True, env=env)

    def project(self):
        d = Path(tempfile.mkdtemp()); shutil.copytree(ROOT / "examples/rainbow", d / "p", ignore=shutil.ignore_patterns("build", "index.html", "README.md"))
        return d / "p"

    def test_estimate_and_build(self):
        p = self.project()
        r = self.run_py("narrate.py", "script.md", "--estimate", cwd=p); self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_py("build.py", ".", cwd=p); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = json.loads((p / "build/timing.json").read_text())
        self.assertIn("light.sun", t["cues"]); self.assertTrue((p / "index.html").exists())

    def test_build_fails_on_unknown_cue(self):
        p = self.project(); self.run_py("narrate.py", "script.md", "--estimate", cwd=p)
        f = p / "scenes/01-light.html"; f.write_text(f.read_text().replace('data-at="sun"', 'data-at="nope"'))
        r = self.run_py("build.py", ".", cwd=p); self.assertNotEqual(r.returncode, 0); self.assertIn("nope", r.stdout)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg missing")
    def test_mock_elevenlabs_roundtrip(self):
        from mock_elevenlabs import H
        srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        p = self.project(); env = dict(os.environ, ELEVENLABS_API_BASE=f"http://127.0.0.1:{srv.server_port}/v1", ELEVENLABS_API_KEY="test")
        try:
            r = self.run_py("narrate.py", "script.md", "--voice", "mock", cwd=p, env=env); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            srv.shutdown()
        t = json.loads((p / "build/timing.json").read_text()); self.assertEqual(t["mode"], "elevenlabs")
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p / "narration.mp3")]))
        self.assertAlmostEqual(dur, t["duration"], delta=0.25)

    def test_site_builds(self):
        p = self.project(); self.run_py("narrate.py", "script.md", "--estimate", cwd=p); self.run_py("build.py", ".", cwd=p)
        d = p.parent; (d / "site.json").write_text(json.dumps({"title": "T", "lang": "en", "courses": [{"id": "c", "title": "C", "videos": [
            {"slug": "v", "title": "V", "dir": "p", "mnemonics": ["Roy G. Biv"], "quiz": [{"q": "Q?", "a": "A"}]}]}]}))
        r = self.run_py("site_build.py", str(d / "site.json")); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((d / "site/c/v/index.html").exists()); self.assertTrue((d / "site/cards.html").exists())


if __name__ == "__main__":
    unittest.main()
