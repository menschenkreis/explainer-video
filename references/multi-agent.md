# Several agents on one course (Claude Code + Codex + …)

The same skill is installed for both (`~/.claude/skills/explainer-video` and `~/.codex/skills/explainer-video` link to ONE
folder – `install.sh` sets that up; never keep two copies). Two agents can work on one course at the same time as long as they
**never edit the same video folder at once**. The course folder (the one with `curriculum.json`) holds the shared state:

| File | What | Who writes |
|---|---|---|
| `curriculum.json` | the plan (videos, fixes, competencies, exercises, publish rule) | one agent at a time, after `ev claim <course> curriculum` |
| `.ev/claims.json` | who works on which video right now | `ev claim` / `ev release` |
| `COURSE_LOG.md` | append-only log: claims, narration runs (+ character count), exports, publishes, decisions | `ev log`, claim/release/publish |
| `.ev/published.json` | what was delivered where, with checksum | `ev publish` |

## The loop (every agent, every time)
1. `ev status <course>` – read it **before** doing anything. It shows stage, owner and warnings per video plus the recent log.
2. `export EV_AGENT=claude` (or `codex`) once per session, then `ev claim <course> <slug> --note "what I'm doing"`.
   If it is claimed by someone else: pick another video. A claim older than 6 h is stale and may be taken over (logged).
3. Work only inside that video's folder (and its own `_tools/vN.py` file, if the course uses the scene DSL).
4. Log anything another agent must know: `ev log <course> "v3: narrated 6120 chars, voice O0x…; listen to scene 'drill'"`.
5. `ev release <course> <slug> --note "done: mp4 exported · next: learner listens"`.

## Rules
* Shared files (`curriculum.json`, `_tools/kit.py`, `learner-profile.json`, `competencies.json`) – claim the pseudo-slug
  (`curriculum`, `kit`, `profile`) before editing; keep edits small and log them.
* Narration costs money: only the agent holding the claim narrates, and only after the learner's OK (see SKILL.md).
* Never "fix" another agent's video while it is claimed – log the problem instead.
* Split work by video, not by step: one agent per video end-to-end (script → scenes → preview → narrate → mp4) is far less
  error-prone than one agent scripting while another narrates.
* The learner can read `COURSE_LOG.md` too – write it for a human.
