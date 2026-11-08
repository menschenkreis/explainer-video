# Learntype brainstorm session (Step 0 – before any content is touched)

**Goal:** discover how *this* learner learns and which analogies they actually understand, so everything that follows
(curriculum order, depth, pace, examples, humour, voice, mnemonics, practice) is tailored. Output: `learner-profile.json`
(machine-readable) + `learner-profile.md` (human-readable, editable, shareable).

Run it as a short, friendly conversation – 5–8 minutes, one or two questions at a time (use `AskUserQuestion` with options when
available; otherwise plain chat). Never quiz or label the person; this is brainstorming *with* them. In a plain terminal, `ev profile <dir>` runs a compact version.

## Flow

### 1. Warm-up – recall, not theory
* “Think of something you learned really well – a skill, a school topic, a game. What made it click?”
* “And something you tried to learn but gave up on – what got in the way?”
Listen for: examples-first vs rules-first, doing vs watching, people vs solitude, pace, anxiety around exams, boredom triggers.
Reflect back in one sentence and let them correct you.

### 2. Goal & context
Goal (exam / job / curiosity), deadline, prior knowledge (beginner / some / advanced), language of study (and of the source material),
what they do for work or hobbies (→ **running example domain**), available time per session (5 / 10 / 15+ min videos).

### 3. Analogy domains – *the heart of the session*
“Which of these worlds do you know well enough that a comparison would make something obvious?” (multi-select, pick 3–5, mark any “no thanks”)
cooking · sports/fitness · music · video games · travel & navigation · building/LEGO/DIY · nature & animals · health & medicine ·
money & shopping · school & everyday life · cars & machines · film & stories · gardening · parenting · military/strategy · (their own).
Then ask for **one concrete thing they know deeply** (a hobby, sport, instrument, job) – that becomes the *home turf* for analogies.

### 4. Calibration test – do the analogies really land?
Pick a neutral concept (e.g. *“modularity”*, *“feedback loop”*, *“trade-off”* – see `analogy-bank.md`) and offer the same idea
through 3 of the learner’s chosen domains (and optionally one they did not choose). Ask: **“Which one made it click fastest? Which felt forced?”**
Record winners and losers. Repeat once with a second concept if the answer is unclear. This beats guessing.

### 5. Style samples – A/B
Show two ~3-sentence openings of the *same* explanation, e.g. (A) calm and structured, (B) lively with a hook and a joke.
Also ask: humour (none / light / lots), pace (slow & thorough / balanced / brisk), depth (overview / standard / deep dive),
how much repetition they like (recaps, mnemonics), preferred practice (quiz / flashcards / explain-it-back / none).
Voice energy follows from this: calm · lively · dramatic (maps to ElevenLabs settings, see below).

### 6. Mnemonics & memory
Acronyms · rhymes · little stories · visual images · “don’t care”. Ask for one example they remember from school to calibrate.

### 7. Play it back & save
Summarise in 6–8 bullets (“You learn best when…”). Ask “What did I get wrong?”. Save both files in the project folder:
`learner-profile.json` and `learner-profile.md`. Tell them they can rerun the session anytime, and that after the first video you’ll
ask which analogies landed and refine the profile.

## `learner-profile.json`
```json
{
  "name": "optional",
  "language": "de", "source_language": "de",
  "goal": "exam | job | curiosity", "deadline": "2026-12-01", "prior_knowledge": "beginner | some | advanced",
  "running_example": {"domain": "online shop", "note": "works in e-commerce"},
  "analogy": {"home_turf": "bouldering", "likes": ["cooking", "sports", "gaming"], "avoid": ["military"], "winners": ["cooking"], "losers": ["music"]},
  "style": {"humour": "none | light | lots", "pace": "slow | balanced | brisk", "depth": "overview | standard | deep",
            "voice_energy": "calm | lively | dramatic", "repetition": "low | medium | high", "mnemonics": ["acronym", "story"]},
  "practice": ["quiz", "flashcards"],
  "session_minutes": 8,
  "notes": "free text from the conversation"
}
```

## How the profile drives production
| profile | effect |
|---|---|
| `language` | narration language, caption language, site language |
| `goal`, `deadline`, `prior_knowledge` | what is cut vs kept, depth, number of videos per week of study time |
| `session_minutes` | target length per video (chars/min budget in `ev plan`) |
| `depth` / `pace` | detail per concept, speech speed (`speed`), number of examples |
| `analogy.winners` / `home_turf` / `likes` | domain of every analogy scene; losers/avoid are never used |
| `running_example` | the recurring case study threaded through all videos |
| `humour` + `voice_energy` | script tone and ElevenLabs settings: calm → `eleven_multilingual_v2`, stability 0.5; lively → `eleven_v3`, stability 0.5 with a few `{curious}`/`{excited}` tags; dramatic → `eleven_v3`, stability 0.0 with more tags |
| `repetition` + `mnemonics` | recap scenes, mnemonic style (acronym / rhyme / story), spaced recap at the start of the next video |
| `practice` | quiz questions and flashcards in the study site |
