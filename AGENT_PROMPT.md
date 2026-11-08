# Paste this into your AI agent

Works with Claude Code and any agent that can run shell commands and read files.

## First time (installs the skill and starts)
```text
Set up and use the "explainer-video" skill for me.

1. Install it (skip if ~/.claude/skills/explainer-video already exists):
   git clone https://github.com/menschenkreis/explainer-video ~/explainer-video && ~/explainer-video/install.sh
   Then run `ev doctor` and help me fix anything it flags (ffmpeg, Chrome, helper venv).
2. Read ~/explainer-video/SKILL.md and follow its workflow.
3. Start with the learntype brainstorm (references/learntype-session.md): interview me about HOW I learn and which analogies I
   understand. One or two questions at a time, include the analogy calibration test, then save learner-profile.json and .md.
4. Ask where my material is (PDFs, Word, slides, notes). Ingest it with `ev ingest`, then synthesise a curriculum for MY profile.
   Show me the outline (videos, lengths, what you cut and why) and wait for my approval before anything costs money.
5. Build each video, check the layout with screenshots, give me a free preview (estimated timing), and iterate with me.

Rules:
- Never ask me to paste my ElevenLabs API key into this chat. Tell me to run `ev key` in my own terminal.
- Before any narration run `ev narrate <dir> --dry-run` and tell me the character count. Wait for my OK.
  Test the voice on ONE scene first; changing voice/model later re-narrates everything.
- Do not publish or upload anything anywhere without asking me first.
- Respect copyright: paraphrase and add your own examples, never copy long passages from my sources.
- If a command fails, stop and tell me; do not export or publish from stale files.
```

## Already installed (short version)
```text
Use the explainer-video skill. My material is in <folder>. Start with the learntype brainstorm (how do I learn, which analogies
click?), then build me a personal curriculum and videos. Show the plan and the narration cost before spending anything.
```

## Just one video, no course
```text
Use the explainer-video skill to make a <8>-minute explainer video about <topic / chapter X of this PDF>, in <language>,
with analogies and mnemonics. Preview it for free first and show me the narration cost before generating the voice.
```
