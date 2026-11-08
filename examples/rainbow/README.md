# Demo: How a Rainbow Forms

A tiny complete project (3 scenes, ~1½ min). Try it without any API key:

```bash
ev preview examples/rainbow        # estimated timing, opens in your browser, costs nothing
```
Click “Video starten” (▶). With narration:

```bash
ev key                             # paste your ElevenLabs key once
ev voices                          # pick a voice id, put it in script.md (voice_id: …)
ev narrate examples/rainbow --dry-run   # shows the character count first
ev all examples/rainbow            # narrate + build + export video.mp4
```
