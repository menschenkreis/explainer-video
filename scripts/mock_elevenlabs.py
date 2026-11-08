#!/usr/bin/env python3
"""Tiny local stand-in for the ElevenLabs API, for testing the pipeline without credits.
   python3 mock_elevenlabs.py &   then:
   ELEVENLABS_API_BASE=http://127.0.0.1:8765/v1 ELEVENLABS_API_KEY=test narrate.py script.md --voice mock
Returns a sine tone whose length follows the text (15 chars/s) plus uniform character timestamps."""
import base64, json, re, subprocess, sys, tempfile, os
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        body = json.dumps({"voices": [{"voice_id": "mock", "name": "Mock", "labels": {}, "category": "test"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        text = req["text"]; cps = 15.0; dur = len(text) / cps + 0.3
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "a.mp3")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=330:duration={dur}", "-ar", "44100", "-ac", "1", "-b:a", "128k", f], check=True)
            audio = base64.b64encode(open(f, "rb").read()).decode()
        st = [i / cps for i in range(len(text))]; en = [(i + 1) / cps for i in range(len(text))]
        out = {"audio_base64": audio, "alignment": {"characters": list(text), "character_start_times_seconds": st, "character_end_times_seconds": en}}
        body = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8765), H).serve_forever()
