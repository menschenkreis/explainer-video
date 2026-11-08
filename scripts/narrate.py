#!/usr/bin/env python3
"""narrate.py  –  script.md  ->  narration.mp3 + build/timing.json   (stdlib only)

The script format (see references/script-format.md):

    ---
    title: My video
    lang: de
    voice_id: <ElevenLabs voice id>        # or env ELEVENLABS_VOICE_ID / --voice
    model: eleven_multilingual_v2
    ---
    ## sceneid | Scene title
    Spoken text. [cue_name] The animation tagged cue_name fires exactly when the next word is spoken.

Every scene is synthesised on its own (cached by content hash, so re-runs cost nothing),
character-level timestamps come back from ElevenLabs, and each [cue] becomes an absolute
time on the final timeline.  --estimate skips the API and fakes timing from text length so the
visuals can be built and checked before spending any credits.

API key: env ELEVENLABS_API_KEY, or a line ELEVENLABS_API_KEY=... in ./.env or
~/.config/explainer-video/.env.  The key is never printed or written to the output.
"""
import argparse, base64, hashlib, json, os, re, shutil, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

API = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io/v1")   # override only for tests (mock_elevenlabs.py)
MARK = re.compile(r"\[([A-Za-z0-9_]+)\]")


# ---------------------------------------------------------------- parsing
def parse_script(path):
    txt = Path(path).read_text(encoding="utf-8")
    meta = {}
    if txt.lstrip().startswith("---"):
        _, fm, txt = txt.lstrip().split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.split(" #")[0].strip()
    scenes, cur = [], None
    for line in txt.splitlines():
        if line.startswith("## "):
            sid, _, title = line[3:].partition("|")
            cur = {"id": sid.strip(), "title": title.strip() or sid.strip(), "lines": []}
            scenes.append(cur)
        elif cur is not None and not line.lstrip().startswith(">") and not line.startswith("# "):
            cur["lines"].append(line)
    for s in scenes:
        raw = " ".join(l.strip() for l in s.pop("lines") if l.strip())
        s["text"], s["marks"], s["display"], s["dmap"] = strip_markers(raw)
    return meta, scenes


TOK = re.compile(r"\[([A-Za-z0-9_]+)\]|\{([^{}]+)\}")


def strip_markers(raw):
    """Returns (spoken, marks, display, dmap).
    [cue] markers are removed (time of next word); {audio tag} is sent as "[audio tag]" for Eleven v3 but hidden from captions.
    spoken = text sent to the API, display = text for captions, dmap[display_index] = spoken_index."""
    out, marks, tags, pos = [], [], [], 0

    def push(chunk):
        for ch in chunk:
            if ch.isspace():
                if out and out[-1] != " ":
                    out.append(" ")
            else:
                out.append(ch)

    for m in TOK.finditer(raw):
        push(raw[pos:m.start()])
        if m.group(1):
            marks.append((m.group(1), len(out)))
        else:
            if out and out[-1] != " ":
                out.append(" ")
            st = len(out); push("[" + m.group(2).strip() + "]"); tags.append((st, len(out)))
            if out and out[-1] != " ":
                out.append(" ")
        pos = m.end()
    push(raw[pos:])
    text = "".join(out)
    lead = len(text) - len(text.lstrip())
    text = text.strip()
    marks = [(n, max(0, min(i - lead, len(text)))) for n, i in marks]
    tags = [(a - lead, b - lead) for a, b in tags]
    intag = set(i for a, b in tags for i in range(a, b))
    disp, dmap = [], []
    for i, ch in enumerate(text):
        if i in intag:
            continue
        if ch == " " and (not disp or disp[-1] == " "):
            continue
        disp.append(ch); dmap.append(i)
    while disp and disp[-1] == " ":
        disp.pop(); dmap.pop()
    return text, marks, "".join(disp), dmap


# ---------------------------------------------------------------- key / API
def load_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k:
        return k.strip()
    for p in (Path(".env"), Path.home() / ".config/explainer-video/.env"):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    return None


def api(method, url, key, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        if "quota_exceeded" in detail:
            sys.exit("ElevenLabs quota exceeded – no credits were spent on this request. Already generated scenes stay cached; "
                     "top up credits (or wait for the monthly reset) and run the same command again to continue.\n" + detail[:300])
        if "missing_permissions" in detail:
            sys.exit("Your ElevenLabs API key lacks a permission (Text to Speech / Voices: Read). Edit the key in the ElevenLabs dashboard.\n" + detail[:300])
        sys.exit(f"ElevenLabs HTTP {e.code}: {detail}")


def list_voices(key):
    data = api("GET", f"{API}/voices", key)
    for v in sorted(data.get("voices", []), key=lambda v: v["name"]):
        lab = v.get("labels") or {}
        print(f'{v["voice_id"]}  {v["name"]:<24} {lab.get("gender","")}/{lab.get("accent","")}/{lab.get("use_case","")}  {v.get("category","")}')


def synth(text, voice, model, settings, key, prev, nxt):
    body = {"text": text, "model_id": model, "voice_settings": settings}
    if model != "eleven_v3":                      # v3 rejects previous_text / next_text
        if prev: body["previous_text"] = prev
        if nxt: body["next_text"] = nxt
    d = api("POST", f"{API}/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128", key, body)
    al = d.get("alignment") or d.get("normalized_alignment")
    return base64.b64decode(d["audio_base64"]), al


# ---------------------------------------------------------------- estimate mode
def estimate_alignment(text, cps):
    starts, ends, t = [], [], 0.0
    for i, ch in enumerate(text):
        d = 1.0 / cps
        starts.append(t); t += d; ends.append(t)
        if ch in ".!?:;" and (i + 1 == len(text) or text[i + 1] == " "): t += 0.28
        elif ch == ",": t += 0.12
    return {"characters": list(text), "character_start_times_seconds": starts, "character_end_times_seconds": ends}


# ---------------------------------------------------------------- timing helpers
def index_maps(s, al):
    """(cue_idx, cap_idx): map spoken-text / display-text indices to alignment indices (v3 may or may not echo the tags)."""
    import bisect
    n = len(al["characters"])
    if n == len(s["text"]):
        return (lambda i: i), (lambda j: s["dmap"][j])
    if n == len(s["display"]):
        return (lambda i: min(bisect.bisect_left(s["dmap"], i), n - 1)), (lambda j: j)
    print(f'  warning: alignment length {n} != text {len(s["text"])}; timing approximated')
    k = n / max(1, len(s["text"]))
    return (lambda i: min(int(i * k), n - 1)), (lambda j: min(int(s["dmap"][j] * k), n - 1))


def cue_time(al, idx):
    st = al["character_start_times_seconds"]
    n = len(st)
    while idx < n and al["characters"][idx].isspace():
        idx += 1
    if idx >= n:
        return al["character_end_times_seconds"][-1]
    return st[idx]


def make_captions(text, al, off, cap_idx, maxlen=84):
    """Sentence captions, long ones split at commas/spaces, timed from the alignment."""
    caps, i, n = [], 0, len(text)
    sent_re = re.compile(r".+?(?:[.!?:](?=\s|$)|$)", re.S)
    for m in sent_re.finditer(text):
        s, e = m.start(), m.end()
        seg = text[s:e]
        if not seg.strip():
            continue
        parts, cut = [], s
        while len(text[cut:e]) > maxlen:
            window = text[cut:cut + maxlen]
            k = max(window.rfind(", "), window.rfind("; "))
            k = k + 1 if k > 30 else window.rfind(" ")
            parts.append((cut, cut + k)); cut = cut + k
        parts.append((cut, e))
        for a, b in parts:
            chunk = text[a:b].strip()
            if not chunk:
                continue
            a2 = a + (len(text[a:b]) - len(text[a:b].lstrip()))
            b2 = min(b, n) - 1
            caps.append({"start": round(off + al["character_start_times_seconds"][cap_idx(a2)], 3),
                         "end": round(off + al["character_end_times_seconds"][cap_idx(b2)] + 0.15, 3), "text": chunk})
    for a, b in zip(caps, caps[1:]):                    # no overlaps
        a["end"] = round(min(a["end"], b["start"]), 3)
    return caps


def ffprobe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def sh(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", nargs="?", default="script.md")
    ap.add_argument("--out", default=".", help="project dir (index.html + narration.mp3 live here; cache in build/)")
    ap.add_argument("--estimate", action="store_true", help="no API calls: estimated timing, no audio")
    ap.add_argument("--cps", type=float, default=14.5, help="characters/second for --estimate (German ~14.5)")
    ap.add_argument("--voice", help="ElevenLabs voice_id (overrides script front matter)")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--only", help="comma-separated scene ids to (re)generate; others must be cached")
    ap.add_argument("--dry-run", action="store_true", help="print what would be synthesised + character count, then stop")
    a = ap.parse_args()

    if a.list_voices:
        key = load_key() or sys.exit("No ELEVENLABS_API_KEY found (env, ./.env or ~/.config/explainer-video/.env)")
        return list_voices(key)

    meta, scenes = parse_script(a.script)
    if not scenes:
        sys.exit("script has no '## id | title' scenes")
    out = Path(a.out); cache = out / "build" / "audio"; cache.mkdir(parents=True, exist_ok=True)
    lead, gap, tail = float(meta.get("lead", .7)), float(meta.get("gap", .7)), float(meta.get("tail", 1.5))
    model = meta.get("model", "eleven_multilingual_v2")
    settings = {"stability": float(meta.get("stability", .5)), "similarity_boost": float(meta.get("similarity", .75)),
                "style": float(meta.get("style", 0)), "use_speaker_boost": True}
    if "speed" in meta: settings["speed"] = float(meta["speed"])
    voice = a.voice or meta.get("voice_id") or os.environ.get("ELEVENLABS_VOICE_ID")

    key = None
    if not a.estimate:
        key = load_key()
        if not key and not a.dry_run:
            sys.exit("No ELEVENLABS_API_KEY found. Put it in the environment, ./.env or ~/.config/explainer-video/.env "
                     "(or use --estimate to preview timing without audio).")
        if not voice:
            sys.exit("No voice. Set voice_id in the script front matter, ELEVENLABS_VOICE_ID, or --voice. "
                     "List voices: narrate.py --list-voices")

    only = set(a.only.split(",")) if a.only else None
    todo_chars = 0
    for i, s in enumerate(scenes):
        s["prev"] = scenes[i - 1]["text"][-300:] if i else ""
        s["next"] = scenes[i + 1]["text"][:300] if i + 1 < len(scenes) else ""
        h = hashlib.sha256(json.dumps([s["text"], voice, model, settings], sort_keys=True).encode()).hexdigest()[:16]
        s["mp3"], s["json"] = cache / f'{s["id"]}-{h}.mp3', cache / f'{s["id"]}-{h}.json'
        s["cached"] = s["mp3"].exists() and s["json"].exists()
        if not s["cached"] and not a.estimate and (only is None or s["id"] in only):
            todo_chars += len(s["text"])
    total = sum(len(s["text"]) for s in scenes)
    print(f"{len(scenes)} scenes, {total} characters total, {todo_chars} to synthesise now"
          f" ({'estimate mode' if a.estimate else 'ElevenLabs ' + model})")
    if a.dry_run:
        return

    timeline, cues, caps, pieces, t0 = {}, {}, [], [], 0.0
    for s in scenes:
        if a.estimate:
            al = estimate_alignment(s["text"], a.cps)
            dur = al["character_end_times_seconds"][-1] + 0.2
        else:
            if not s["cached"]:
                if only is not None and s["id"] not in only:
                    sys.exit(f'scene {s["id"]} is not cached; run without --only first')
                print(f'  synthesising {s["id"]} ({len(s["text"])} chars)…', flush=True)
                audio, al = synth(s["text"], voice, model, settings, key, s["prev"], s["next"])
                s["mp3"].write_bytes(audio); s["json"].write_text(json.dumps(al))
            al = json.loads(s["json"].read_text())
            dur = ffprobe_dur(s["mp3"])
        is_last = s is scenes[-1]
        pad = gap + (tail if is_last else 0)
        total_len = lead + dur + pad
        timeline[s["id"]] = {"start": round(t0, 3), "end": round(t0 + total_len, 3), "title": s["title"],
                             "speech_start": round(t0 + lead, 3), "speech_end": round(t0 + lead + dur, 3)}
        cue_idx, cap_idx = index_maps(s, al)
        for name, idx in s["marks"]:
            key_ = f'{s["id"]}.{name}'
            if key_ in cues:
                print(f"  warning: duplicate cue {key_}")
            cues[key_] = round(t0 + lead + cue_time(al, cue_idx(idx)), 3)
        caps += make_captions(s["display"], al, t0 + lead, cap_idx)
        pieces.append((s, lead, pad)); t0 += total_len

    audio_name = None
    if not a.estimate:
        wdir = out / "build" / "wav"; wdir.mkdir(parents=True, exist_ok=True)
        wavs, real = [], 0.0
        for s, ld, pad in pieces:
            w = wdir / f'{s["id"]}.wav'
            sh("ffmpeg", "-y", "-i", str(s["mp3"]), "-af", f"adelay={int(ld*1000)}:all=1,apad=pad_dur={pad}", "-ar", "44100", "-ac", "1", str(w))
            wavs.append(w); real += ffprobe_dur(w)
        lst = wdir / "list.txt"; lst.write_text("".join(f"file '{w.resolve()}'\n" for w in wavs))
        sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-b:a", "160k", str(out / "narration.mp3"))
        audio_name = "narration.mp3"
        drift = real - t0
        print(f"audio {real:.1f}s vs timeline {t0:.1f}s (drift {drift*1000:+.0f} ms)")
        if abs(drift) > 0.15:
            print("  note: drift >150 ms; timeline uses ffprobe durations of the scene files, re-run if you edited audio")
    else:
        old = out / "narration.mp3"
        if old.exists():
            old.unlink()          # stale audio from an earlier real run would desync the estimated timeline

    timing = {"mode": "estimate" if a.estimate else "elevenlabs", "title": meta.get("title", ""), "lang": meta.get("lang", "de"),
              "duration": round(t0, 3), "audio": audio_name, "order": [s["id"] for s in scenes],
              "scenes": timeline, "cues": cues, "captions": caps}
    (out / "build").mkdir(exist_ok=True)
    (out / "build" / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))
    print(f'timing.json written: {t0:.1f}s ({t0/60:.1f} min), {len(cues)} cues, {len(caps)} captions, mode={timing["mode"]}')


if __name__ == "__main__":
    main()
