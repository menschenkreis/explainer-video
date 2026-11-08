#!/usr/bin/env python3
"""ical.py – read a study calendar (ICS/iCal feed, e.g. OLAT/OpenOlat "aggregated" feed) and turn it into study blocks.

  ical.py add <url>                 save the feed URL privately (~/.config/explainer-video/calendar.json, permissions 600)
  ical.py fetch [--out DIR]         download + parse  → DIR/calendar/events.json     (DIR default: .)
  ical.py blocks [--out DIR] [--days N] [--past N] [--gap D]
                                    group events into study blocks → DIR/calendar/study-blocks.json and print an outline
  ical.py file <x.ics> [--out DIR]  same as fetch, from a local .ics file

The feed URL is a secret (it contains an access token). It is never printed in full, never written into project folders and
must never be committed. stdlib only.
"""
import argparse, json, os, re, sys, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

CFG = Path.home() / ".config/explainer-video/calendar.json"
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
BLOCK_RE = re.compile(r"\b(block|modul|module|semester|woche|week|kw)\s*[-:]?\s*(\d+)", re.I)


def mask(url):
    u = urlparse(url); return f"{u.scheme}://{u.netloc}{u.path.rsplit('/', 2)[0]}/…"


def unfold(text):
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line[:1] in (" ", "\t") and out: out[-1] += line[1:]
        else: out.append(line)
    return out


def unescape(v): return v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def parse_dt(value, params):
    """Return (datetime|date, all_day). TZID → zoneinfo when available, 'Z' → UTC, otherwise floating (treated as local)."""
    if "VALUE=DATE" in params.upper() or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value[:8], "%Y%m%d").date(), True
    fmt = "%Y%m%dT%H%M%S"
    dt = datetime.strptime(value.rstrip("Z"), fmt)
    if value.endswith("Z"): return dt.replace(tzinfo=timezone.utc), False
    m = re.search(r"TZID=([^;:]+)", params)
    if m:
        try:
            from zoneinfo import ZoneInfo
            return dt.replace(tzinfo=ZoneInfo(m.group(1))), False
        except Exception: pass
    return dt, False


def parse_ics(text):
    events, cur = [], None
    for raw in unfold(text):
        if raw == "BEGIN:VEVENT": cur = {}
        elif raw == "END:VEVENT" and cur is not None:
            events.append(cur); cur = None
        elif cur is not None and ":" in raw:
            head, _, val = raw.partition(":"); name, _, params = head.partition(";"); cur.setdefault(name.upper(), []).append((params, val))
    out = []
    for e in events:
        g = lambda k: (e.get(k) or [("", "")])[0]
        try:
            sp, sv = g("DTSTART")
            if not sv: continue
            start, allday = parse_dt(sv, sp)
            ep, ev = g("DTEND")
            end = parse_dt(ev, ep)[0] if ev else None
        except Exception:
            continue
        desc = unescape(g("DESCRIPTION")[1]); loc = unescape(g("LOCATION")[1]); summ = unescape(g("SUMMARY")[1]).strip()
        urls = list(dict.fromkeys(URL_RE.findall(desc + " " + g("URL")[1] + " " + loc)))
        out.append({"uid": g("UID")[1], "summary": summ, "start": start, "end": end, "all_day": allday, "location": loc, "description": desc, "links": urls,
                    "categories": [c for _, v in (e.get("CATEGORIES") or []) for c in v.split(",") if c], "rrule": g("RRULE")[1], "status": g("STATUS")[1]})
    return expand(out)


def expand(events, horizon_days=400):
    """Expand simple DAILY/WEEKLY recurrences (INTERVAL, COUNT, UNTIL, BYDAY) so blocks see every occurrence."""
    res = []
    for e in events:
        res.append(e)
        r = dict(p.split("=", 1) for p in e["rrule"].split(";") if "=" in p) if e["rrule"] else {}
        if r.get("FREQ") not in ("DAILY", "WEEKLY"): continue
        step = int(r.get("INTERVAL", 1)); count = int(r.get("COUNT", 0)) or 10 ** 6
        s = e["start"]; sd = s if isinstance(s, datetime) else datetime.combine(s, datetime.min.time())
        until = None
        if "UNTIL" in r:
            try: until = parse_dt(r["UNTIL"], "")[0]
            except Exception: pass
        days = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
        byday = [days[d[-2:]] for d in r.get("BYDAY", "").split(",") if d[-2:] in days] or [sd.weekday()]
        dur = (e["end"] - e["start"]) if e["end"] and e["start"] and type(e["end"]) == type(e["start"]) else None
        n, cur = 1, sd
        limit = sd + timedelta(days=horizon_days)
        while n < count:
            cur = cur + timedelta(days=1 if r["FREQ"] == "DAILY" else 1)
            if cur > limit: break
            week = (cur.date() - sd.date()).days // 7
            if r["FREQ"] == "DAILY" and (cur.date() - sd.date()).days % step: continue
            if r["FREQ"] == "WEEKLY" and (week % step or cur.weekday() not in byday): continue
            if until is not None and cur.date() > (until.date() if isinstance(until, datetime) else until): break
            ne = dict(e); ne["start"] = cur if isinstance(s, datetime) else cur.date()
            if dur is not None: ne["end"] = ne["start"] + dur
            ne["rrule"] = ""; res.append(ne); n += 1
    return res


def iso(v): return v.isoformat() if v is not None else None
def day(v): return v.date() if isinstance(v, datetime) else v


TITLE_RE = re.compile(r"^(?P<course>.+?)(?:\s+[-–—]\s+(?P<teacher>[^(]+?))?\s*(?:\((?P<code>[^)]*)\))?\s*$")


def split_title(summary):
    """'Systems Engineering - Jane Doe (CLASS-X SYENFI-S2)' → course, teacher, code (works for OLAT/OpenOlat exports; falls back gracefully)."""
    m = TITLE_RE.match(summary.strip()); d = m.groupdict() if m else {}
    course = re.sub(r"\s+", " ", (d.get("course") or summary)).strip()
    return course, re.sub(r"\s+", " ", d.get("teacher") or "").strip(), (d.get("code") or "").strip()


def title_key(summary):
    course, _, _ = split_title(summary)
    m = BLOCK_RE.search(summary)
    return course[:60], (f"{m.group(1).title()} {m.group(2)}" if m else None)


def blocks(events, gap_days=10):
    """Group events into study blocks: same course key (and 'Block N' marker if present), split on gaps > gap_days."""
    groups = {}
    for ev in sorted(events, key=lambda e: day(e["start"])):
        k, bn = title_key(ev["summary"])
        groups.setdefault((k, bn), []).append(ev)
    out = []
    for (k, bn), evs in groups.items():
        cluster = [evs[0]]
        for ev in evs[1:]:
            if (day(ev["start"]) - day(cluster[-1]["start"])).days > gap_days:
                out.append((k, bn, cluster)); cluster = []
            cluster.append(ev)
        out.append((k, bn, cluster))
    res = []
    for k, bn, evs in sorted(out, key=lambda x: day(x[2][0]["start"])):
        teachers = sorted({split_title(e["summary"])[1] for e in evs if split_title(e["summary"])[1]}); codes = sorted({split_title(e["summary"])[2] for e in evs if split_title(e["summary"])[2]})
        topics = list(dict.fromkeys(e["summary"] for e in evs))
        res.append({"id": re.sub(r"[^a-z0-9]+", "-", f"{k}-{bn or day(evs[0]['start'])}".lower()).strip("-"), "course": k, "block": bn,
                    "first": iso(day(evs[0]["start"])), "last": iso(day(evs[-1]["start"])), "sessions": len(evs), "teachers": teachers, "codes": codes, "topics": topics[:12],
                    "locations": sorted({e["location"] for e in evs if e["location"]})[:5],
                    "links": list(dict.fromkeys(l for e in evs for l in e["links"]))[:20],
                    "descriptions": [e["description"][:400] for e in evs if e["description"]][:5],
                    "events": [{"date": iso(e["start"]), "summary": e["summary"]} for e in evs]})
    return res


def load_cfg():
    if not CFG.exists(): sys.exit("No calendar saved. Run:  ev calendar add <ics-url>")
    return json.loads(CFG.read_text())["url"]


def fetch_text(url):
    url = re.sub(r"^webcal", "http", url) if url.startswith("webcal") else url
    req = urllib.request.Request(url, headers={"User-Agent": "explainer-video/1.0", "Accept": "text/calendar,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def read_events(path):
    return [{**e, "start": datetime.fromisoformat(e["start"]) if "T" in e["start"] else date.fromisoformat(e["start"])} for e in json.loads(path.read_text())]


def save_events(path, evs):
    path.write_text(json.dumps([{**e, "start": iso(e["start"]), "end": iso(e["end"])} for e in evs], ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "fetch", "blocks", "file"]); ap.add_argument("arg", nargs="?")
    ap.add_argument("--out", default="."); ap.add_argument("--days", type=int, default=120, help="blocks: upcoming window in days")
    ap.add_argument("--past", type=int, default=30, help="blocks: look back this many days"); ap.add_argument("--gap", type=int, default=10, help="blocks: days of silence that start a new block")
    ap.add_argument("--refresh", action="store_true", help="blocks: download the feed again")
    a = ap.parse_args()
    out = Path(a.out) / "calendar"; out.mkdir(parents=True, exist_ok=True); ev_path = out / "events.json"
    if a.cmd == "add":
        if not a.arg or not re.match(r"^(https?|webcals?)://", a.arg): sys.exit("usage: ical.py add <https://…/feed.ics>")
        CFG.parent.mkdir(parents=True, exist_ok=True); CFG.write_text(json.dumps({"url": a.arg})); CFG.chmod(0o600)
        print(f"saved (private, mode 600): {mask(a.arg)}"); return
    if a.cmd == "file":
        events = parse_ics(Path(a.arg).read_text(encoding="utf-8", errors="replace")); save_events(ev_path, events); print(f"{len(events)} events → {ev_path}"); return
    if a.cmd == "fetch" or a.refresh or not ev_path.exists():
        events = parse_ics(fetch_text(load_cfg())); save_events(ev_path, events); print(f"{len(events)} events → {ev_path}")
        if a.cmd == "fetch": return
    else:
        events = read_events(ev_path)
    today = date.today(); lo, hi = today - timedelta(days=a.past), today + timedelta(days=a.days)
    sel = [e for e in events if lo <= day(e["start"]) <= hi]
    bl = blocks(sel, a.gap)
    (out / "study-blocks.json").write_text(json.dumps(bl, ensure_ascii=False, indent=1))
    print(f"\n{len(sel)} events between {lo} and {hi} → {len(bl)} study blocks  ({out/'study-blocks.json'})\n")
    for b in bl:
        print(f"▸ {b['course']}{(' · ' + b['block']) if b['block'] else ''}   {b['first']} → {b['last']}   ({b['sessions']} sessions)")
        if b["teachers"] or b["codes"]: print(f"    {', '.join(b['teachers'])}  [{', '.join(b['codes'])}]")
        print("    sessions: " + ", ".join(e["date"][:16].replace("T", " ") for e in b["events"][:8]))
        for l in b["links"][:3]: print(f"    link: {l}")
        if b["links"]: print("    → scan the link(s) for preparation material (browser skill)")


if __name__ == "__main__":
    main()
