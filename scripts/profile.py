#!/usr/bin/env python3
"""profile.py <dir>  –  compact terminal version of the learntype brainstorm session (Claude Code runs the richer conversational one,
see references/learntype-session.md).  Writes learner-profile.json + learner-profile.md into <dir>."""
import json, sys
from pathlib import Path

DOMAINS = ["cooking", "sports/fitness", "music", "video games", "travel & navigation", "building/LEGO/DIY", "nature & animals",
           "health & medicine", "money & shopping", "cars & machines", "film & stories", "gardening"]


def ask(q, opts=None, multi=False, default=None):
    print("\n" + q)
    if opts:
        for i, o in enumerate(opts, 1): print(f"  {i}) {o}")
        raw = input("> ").strip()
        if not raw and default is not None: return default
        idx = [int(x) - 1 for x in raw.replace(",", " ").split() if x.isdigit() and 0 < int(x) <= len(opts)]
        return [opts[i] for i in idx] if multi else (opts[idx[0]] if idx else default)
    return input("> ").strip()


def main():
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "."); d.mkdir(parents=True, exist_ok=True)
    print("Learntype brainstorm – 2 minutes. Press Enter to skip a question.")
    recall = ask("Think of something you learned really well. What made it click?")
    stuck = ask("Something you gave up on – what got in the way?")
    lang = ask("Language for the videos?", ["de", "en", "fr", "es", "it"], default="en")
    goal = ask("Your goal?", ["exam", "job", "curiosity"], default="curiosity")
    prior = ask("Prior knowledge of the topic?", ["beginner", "some", "advanced"], default="beginner")
    work = ask("What do you do for work or as a hobby? (becomes the running example)")
    likes = ask("Which worlds do you know well enough for comparisons? (several, e.g. 1 3 4)", DOMAINS, multi=True, default=[])
    home = ask("One thing you know deeply (sport, instrument, job)?")
    avoid = ask("Any analogy worlds you dislike? (several)", DOMAINS, multi=True, default=[])
    humour = ask("Humour?", ["none", "light", "lots"], default="light")
    energy = ask("Voice energy?", ["calm", "lively", "dramatic"], default="lively")
    pace = ask("Pace?", ["slow", "balanced", "brisk"], default="balanced")
    depth = ask("Depth?", ["overview", "standard", "deep"], default="standard")
    rep = ask("Repetition (recaps, mnemonics)?", ["low", "medium", "high"], default="medium")
    mn = ask("Memory aids you like?", ["acronym", "rhyme", "story", "visual image"], multi=True, default=["acronym"])
    pr = ask("Practice?", ["quiz", "flashcards", "explain-it-back", "none"], multi=True, default=["quiz"])
    mins = ask("Ideal video length in minutes?", ["5", "8", "10", "15"], default="8")
    prof = {"language": lang, "source_language": lang, "goal": goal, "prior_knowledge": prior,
            "running_example": {"domain": work or "everyday life", "note": ""},
            "analogy": {"home_turf": home, "likes": likes, "avoid": avoid, "winners": [], "losers": []},
            "style": {"humour": humour, "pace": pace, "depth": depth, "voice_energy": energy, "repetition": rep, "mnemonics": mn},
            "practice": pr, "session_minutes": int(mins), "notes": f"Click: {recall} | Stuck: {stuck}"}
    (d / "learner-profile.json").write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# Learner profile
* **Learns best when:** {recall or '–'}
* **Gets stuck when:** {stuck or '–'}
* **Goal:** {goal} · prior knowledge: {prior} · language: {lang}
* **Running example:** {work or '–'}
* **Analogies from:** {', '.join(likes) or '–'} (home turf: {home or '–'}; avoid: {', '.join(avoid) or '–'})
* **Style:** humour {humour}, voice {energy}, pace {pace}, depth {depth}, repetition {rep}
* **Memory aids:** {', '.join(mn)} · **Practice:** {', '.join(pr)} · **Video length:** {mins} min
"""
    (d / "learner-profile.md").write_text(md, encoding="utf-8")
    print(f"\nsaved {d/'learner-profile.json'} and learner-profile.md – edit them any time, or run the richer session in Claude Code.")


if __name__ == "__main__":
    main()
