#!/usr/bin/env python3
"""plan.py <curriculum.json> [--scaffold] [--profile learner-profile.json]

Validates curriculum.json, prints the course outline with time budget, and with --scaffold creates one project per video
(script.md skeleton in the learner's tone + a starter scene) plus a site.json for `ev site`.
Schema: references/curriculum-synthesis.md.   Written by the model during curriculum synthesis; reviewed by the learner first.
"""
import argparse, json, sys
from pathlib import Path

CPM = {"de": 780, "en": 900, "fr": 850, "es": 900, "it": 850}       # narrated characters per minute (measured: German v3 ≈ 760–800)
VOICE = {"calm": ("eleven_multilingual_v2", 0.5), "lively": ("eleven_v3", 0.5), "dramatic": ("eleven_v3", 0.0)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("curriculum"); ap.add_argument("--scaffold", action="store_true"); ap.add_argument("--profile")
    a = ap.parse_args()
    cp = Path(a.curriculum).resolve(); base = cp.parent; cur = json.loads(cp.read_text(encoding="utf-8"))
    pp = Path(a.profile) if a.profile else base / cur.get("profile", "learner-profile.json")
    prof = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else {}
    lang = cur.get("language") or prof.get("language", "en"); cpm = CPM.get(lang, 800)
    style = prof.get("style", {}); model, stab = VOICE.get(style.get("voice_energy", "lively"), VOICE["lively"])
    problems, total, n = [], 0, 0
    print(f"{cur['title']}  [{lang}]  profile: {'yes' if prof else 'MISSING (run the learntype session first)'}")
    for m in cur["modules"]:
        print(f"\n▸ {m['title']}")
        for v in m["videos"]:
            n += 1; mins = v.get("est_minutes", 0); total += mins
            for k in ("slug", "title", "objectives"):
                if not v.get(k): problems.append(f"{v.get('slug', '?')}: missing '{k}'")
            if not v.get("analogy"): problems.append(f"{v['slug']}: no analogy chosen")
            if prof.get("session_minutes") and mins > prof["session_minutes"] * 1.3:
                problems.append(f"{v['slug']}: {mins} min is well above the learner's session length ({prof['session_minutes']} min)")
            bad = set(prof.get("analogy", {}).get("avoid", []) + prof.get("analogy", {}).get("losers", []))
            if v.get("analogy", {}).get("domain") in bad: problems.append(f"{v['slug']}: analogy domain '{v['analogy']['domain']}' is on the learner's avoid list")
            print(f"  {n:2d}. {v['title']}  ·  {mins} min  ·  ≈{int(mins * cpm)} characters  ·  analogy: {v.get('analogy', {}).get('domain', '–')}")
    # study-block awareness: videos should be watchable BEFORE the session they prepare for
    from datetime import date as _d
    for m in cur["modules"]:
        for v in m["videos"]:
            blk = v.get("block") or m.get("block")
            if isinstance(blk, dict) and blk.get("first_session") and v.get("ready_by") and v["ready_by"] > blk["first_session"]:
                problems.append(f"{v['slug']}: ready_by {v['ready_by']} is after the first session of its block ({blk['first_session']})")
    print(f"\n{n} videos, {total} min total, {cpm} narrated characters/min for '{lang}'")
    for p in problems: print("  ⚠", p)
    if not a.scaffold:
        return 1 if problems else 0
    site = {"title": cur["title"], "subtitle": cur.get("subtitle", ""), "lang": lang, "notice": cur.get("notice", ""), "courses": []}
    for m in cur["modules"]:
        course = {"id": m["id"], "title": m["title"], "videos": []}
        for v in m["videos"]:
            d = base / "videos" / v["slug"]; (d / "scenes").mkdir(parents=True, exist_ok=True); (d / "build").mkdir(exist_ok=True)
            if not (d / "script.md").exists():
                refs = "; ".join(f"{r.get('file')} p.{r.get('pages')}" for r in v.get("source_refs", []))
                (d / "script.md").write_text(f"""---
title: {v['title']}
lang: {lang}
model: {model}
# voice_id: <ev voices>
stability: {stab}
lead: 0.7
gap: 0.6
tail: 2.0
---
> Objectives: {'; '.join(v.get('objectives', []))}
> Sources: {refs}
> Analogy ({v.get('analogy', {}).get('domain', '')}): {v.get('analogy', {}).get('idea', '')}
> Example: {v.get('example', '')} · Mnemonic: {v.get('mnemonic', '')} · target ≈ {int(v.get('est_minutes', 8) * cpm)} characters

## intro | Intro
{{curious}} Write the hook here. [hook] …
""", encoding="utf-8")
            sc = d / "scenes" / "01-intro.html"
            if not sc.exists():
                sc.write_text(f'''<section class="scene" data-scene="intro" data-part="{m['title']}">
  <div class="head"><span class="kick" data-at="@start+0.2" data-fx="pop">{n}</span><h2 data-at="hook" data-fx="rise">{v['title']}</h2></div>
  <div class="body"></div>
</section>
''', encoding="utf-8")
            course["videos"].append({"slug": v["slug"], "title": v["title"], "dir": f"videos/{v['slug']}", "summary": v.get("summary", "; ".join(v.get("objectives", []))),
                                     "mnemonics": [v["mnemonic"]] if v.get("mnemonic") else [], "quiz": v.get("quiz", [])})
        site["courses"].append(course)
    (base / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nscaffolded {n} projects under {base/'videos'} and wrote site.json")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
