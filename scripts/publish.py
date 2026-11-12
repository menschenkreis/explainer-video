#!/usr/bin/env python3
"""publish.py <course-dir> [--only slug,slug] [--yes] [--force] [--agent NAME]

Copies each finished video's MP4 to the learner's delivery folder (e.g. a synced Google Drive folder) under ONE naming rule,
and moves older versions into an archive sub-folder instead of overwriting them. Without --yes it only prints the plan.

curriculum.json (course-level, a module may override it, a video may set "publish_name"):
  "publish": {"to": "/…/My Drive/Course/Erklär Videos/Block 1",
              "name": "Systems-Engineering_Block1_V{n}_{short}.mp4",
              "archive": "_Archiv"}
  video: "short": "Die-Landkarte" (default: title after ':' → ASCII, hyphens), "n": 1 (default: position in the course),
         "replaces": ["Systems-Engineering_Kap3_Teil1_….mp4"]   older files of the same content → archived on publish
Placeholders: {n} {nn} {slug} {short} {block} {module} {course}.
The MP4 is <video-dir>/video.mp4, else the newest *.mp4 there. A video whose MP4 is older than its narration is refused
(stale export) unless --force. Each publish is appended to COURSE_LOG.md and recorded in .ev/published.json.
"""
import argparse, hashlib, json, re, shutil, sys, unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coord import load_curriculum, videos, video_dir, newest_mp4, log, agent_name  # noqa: E402

UML = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss", "&": "und"}


def short_name(title):
    t = title.split(":", 1)[1] if ":" in title else title
    t = "".join(UML.get(ch, ch) for ch in t.strip())
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"-{2,}", "-", re.sub(r"[^A-Za-z0-9]+", "-", t)).strip("-")[:60]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def plan(base, cur, only=None, force=False):
    acts, warns = [], []
    for n, m, v in videos(cur):
        if only and v["slug"] not in only:
            continue
        cfg = {**cur.get("publish", {}), **m.get("publish", {})}
        if not cfg.get("to"):
            warns.append(f"{v['slug']}: no publish target (set \"publish\": {{\"to\": …, \"name\": …}} in curriculum.json)"); continue
        d = video_dir(base, v); mp4 = newest_mp4(d)
        if not mp4:
            warns.append(f"{v['slug']}: no MP4 yet (ev mp4 {d})"); continue
        nar = d / "narration.mp3"
        if nar.exists() and mp4.stat().st_mtime < nar.stat().st_mtime and not force:
            warns.append(f"{v['slug']}: {mp4.name} is older than narration.mp3 – re-export first (or --force)"); continue
        blk = v.get("block") or m.get("block") or {}
        fields = dict(n=v.get("n", n), nn=f"{v.get('n', n):02d}", slug=v["slug"], short=v.get("short") or short_name(v["title"]),
                      block=blk.get("id", "") if isinstance(blk, dict) else str(blk), module=m.get("id", ""), course=cur.get("short", ""))
        name = v.get("publish_name") or cfg.get("name", "{slug}.mp4").format(**fields)
        to = Path(cfg["to"]).expanduser(); arch = to / cfg.get("archive", "_Archiv")
        acts.append(dict(slug=v["slug"], src=mp4, dst=to / name, archive=arch, replaces=[to / r for r in v.get("replaces", []) if r != name]))
    return acts, warns


def apply(base, acts, agent, yes):
    rec_p = base / ".ev" / "published.json"
    rec = json.loads(rec_p.read_text(encoding="utf-8")) if rec_p.exists() else {}
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    for a in acts:
        steps = []
        old = [a["dst"]] if a["dst"].exists() else []
        if old and a["dst"].stat().st_size == a["src"].stat().st_size and sha(a["dst"]) == sha(a["src"]):
            print(f"= {a['slug']}: {a['dst'].name} is up to date"); old = None
        for o in (old or []) + [r for r in a["replaces"] if r.exists()]:
            steps.append(("archive", o, a["archive"] / f"{o.stem}__{stamp}{o.suffix}"))
        if old is not None:
            steps.append(("copy", a["src"], a["dst"]))
        for kind, s, t in steps:
            print(f"{'  ' if yes else '  (dry) '}{kind:<7} {s.name}  →  {t.parent.name}/{t.name}")
            if yes:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(s), str(t)) if kind == "archive" else shutil.copy2(s, t)
        if yes and steps:
            rec[a["slug"]] = {"file": str(a["dst"]), "at": datetime.now().astimezone().isoformat(timespec="seconds"), "sha256": sha(a["dst"])}
            log(base, agent, f"published `{a['slug']}` → {a['dst'].name}" + (f" (archived {sum(1 for k, *_ in steps if k == 'archive')} old)" if any(k == "archive" for k, *_ in steps) else ""))
    if yes:
        rec_p.parent.mkdir(parents=True, exist_ok=True); rec_p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    elif acts:
        print("\nDry run – nothing copied. Run again with --yes once the learner agrees.")


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("course"); ap.add_argument("--only"); ap.add_argument("--yes", action="store_true")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--agent")
    a = ap.parse_args(argv)
    base = Path(a.course).resolve(); cur = load_curriculum(base)
    acts, warns = plan(base, cur, set(a.only.split(",")) if a.only else None, a.force)
    for w in warns:
        print("  ⚠", w)
    apply(base, acts, agent_name(a.agent), a.yes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
