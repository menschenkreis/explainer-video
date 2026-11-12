#!/usr/bin/env python3
"""coord.py – let several agents (Claude Code, Codex, …) work on one course without overwriting each other.

  coord.py claim   <course-dir> <slug> [--agent NAME] [--note TEXT] [--force]   take a video before touching its files
  coord.py release <course-dir> <slug> [--agent NAME] [--note TEXT]            give it back (note = what is done / next)
  coord.py log     <course-dir> "message" [--agent NAME]                       append one line to COURSE_LOG.md
  coord.py status  <course-dir>                                                every video: owner, files present, stage

<course-dir> is the folder with curriculum.json. State lives in <course-dir>/.ev/claims.json and <course-dir>/COURSE_LOG.md
(plain files, so any agent – or the learner – can read them). Agent name: --agent, else $EV_AGENT, else "agent".
A claim older than 6 hours counts as stale and may be taken over (the takeover is logged).
"""
import argparse, json, os, sys
from datetime import datetime, timedelta
from pathlib import Path

STALE = timedelta(hours=6)


def now():
    return datetime.now().astimezone().replace(microsecond=0)


def agent_name(a):
    return a or os.environ.get("EV_AGENT") or "agent"


def load_curriculum(base):
    p = base / "curriculum.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"modules": []}


def videos(cur):
    n = 0
    for m in cur.get("modules", []):
        for v in m.get("videos", []):
            n += 1
            yield n, m, v


def video_dir(base, v):
    """explicit "dir" → videos/<slug> (ev plan --scaffold) → <slug> (hand-made courses)"""
    if v.get("dir"):
        return (base / v["dir"]).resolve()
    for d in (base / "videos" / v["slug"], base / v["slug"]):
        if d.exists():
            return d
    return base / "videos" / v["slug"]


def newest_mp4(d):
    if (d / "video.mp4").exists():
        return d / "video.mp4"
    mp4 = sorted(d.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True) if d.exists() else []
    return mp4[0] if mp4 else None


def stage(d):
    """script → preview → narrated → mp4 (with a warning when the MP4 is older than the narration)"""
    if not (d / "script.md").exists():
        return "–", ""
    st = "script"
    if (d / "index.html").exists():
        st = "preview"
    if (d / "narration.mp3").exists():
        st = "narrated"
    mp4, warn = newest_mp4(d), ""
    if mp4:
        st = "mp4"
        if (d / "narration.mp3").exists() and mp4.stat().st_mtime < (d / "narration.mp3").stat().st_mtime:
            warn = "MP4 older than narration – re-export"
    return st, warn


def claims_path(base):
    return base / ".ev" / "claims.json"


def read_claims(base):
    p = claims_path(base)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_claims(base, c):
    p = claims_path(base); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8"); tmp.replace(p)


def log(base, agent, msg):
    p = base / "COURSE_LOG.md"
    if not p.exists():
        p.write_text("# Course log\n\nAppend-only. One line per event: claims, releases, narration, exports, publishes, decisions.\n\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {now():%Y-%m-%d %H:%M} **{agent}** {msg}\n")


def is_stale(c):
    try:
        return now() - datetime.fromisoformat(c["since"]) > STALE
    except Exception:
        return True


def claim(base, slug, agent, note="", force=False):
    c = read_claims(base); cur = c.get(slug)
    if cur and cur["agent"] != agent and not force and not is_stale(cur):
        print(f"✗ {slug} is claimed by {cur['agent']} since {cur['since']}" + (f" ({cur['note']})" if cur.get("note") else "")
              + "\n  Work on another video, or ask the learner; --force only if they say so.")
        return 1
    if cur and cur["agent"] != agent:
        log(base, agent, f"took over `{slug}` from {cur['agent']} ({'stale' if is_stale(cur) else 'forced'})")
    c[slug] = {"agent": agent, "since": now().isoformat(), "note": note}
    write_claims(base, c); log(base, agent, f"claimed `{slug}`" + (f" – {note}" if note else ""))
    print(f"✓ {slug} claimed by {agent}")
    return 0


def release(base, slug, agent, note=""):
    c = read_claims(base); cur = c.get(slug)
    if not cur:
        print(f"{slug} was not claimed"); return 0
    if cur["agent"] != agent:
        print(f"✗ {slug} is claimed by {cur['agent']}, not {agent}"); return 1
    del c[slug]; write_claims(base, c); log(base, agent, f"released `{slug}`" + (f" – {note}" if note else ""))
    print(f"✓ {slug} released"); return 0


def status(base):
    cur, c = load_curriculum(base), read_claims(base)
    pp = base / ".ev" / "published.json"
    published = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else {}
    print(f"{cur.get('title', base.name)}   ({base})")
    for n, m, v in videos(cur):
        d = video_dir(base, v); st, warn = stage(d)
        who = c.get(v["slug"])
        owner = f"{who['agent']}{' (stale)' if is_stale(who) else ''}" if who else "free"
        p = published.get(v["slug"])
        pub = f" · published {p['at'][:10]}" if p else ""
        mp4 = newest_mp4(d)
        if p and mp4 and mp4.stat().st_mtime > datetime.fromisoformat(p["at"]).timestamp() + 5:
            warn = (warn + "; " if warn else "") + "newer MP4 than the published one – ev publish"
        print(f"  {n:2d}. {v['slug']:<28} {st:<9} {owner:<16}{pub}" + (f"  ⚠ {warn}" if warn else ""))
    extra = sorted(set(c) - {v["slug"] for _, _, v in videos(cur)})
    for s in extra:
        print(f"      {s:<28} (not in curriculum) claimed by {c[s]['agent']}")
    lp = base / "COURSE_LOG.md"
    if lp.exists():
        lines = [x for x in lp.read_text(encoding="utf-8").splitlines() if x.startswith("- ")]
        if lines:
            print("\nrecent log:"); [print("  " + x[2:]) for x in lines[-8:]]
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["claim", "release", "log", "status"]); ap.add_argument("course")
    ap.add_argument("arg", nargs="?"); ap.add_argument("--agent"); ap.add_argument("--note", default=""); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    base = Path(a.course).resolve()
    if not base.is_dir():
        sys.exit(f"{base} is not a directory")
    ag = agent_name(a.agent)
    if a.cmd == "status":
        return status(base)
    if not a.arg:
        what = '"message"' if a.cmd == "log" else "<slug>"
        sys.exit(f"usage: ev {a.cmd} <course-dir> {what}")
    if a.cmd == "log":
        log(base, ag, a.arg); return 0
    return claim(base, a.arg, ag, a.note, a.force) if a.cmd == "claim" else release(base, a.arg, ag, a.note)


if __name__ == "__main__":
    sys.exit(main())
