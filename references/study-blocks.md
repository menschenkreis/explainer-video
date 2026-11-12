# Study blocks: find out what each block is about, and what to prepare (Step 1b)

Goal: build the course **around the learner's real study plan** – for every block, what is taught, when, and what has to be
read/prepared – and make the videos ready *before* each block.

## 1. Connect the study calendar (iCal / ICS feed)
```bash
ev calendar add "<https://…/your-calendar.ics>"     # OpenOlat/OLAT "aggregated" feed, Google/Outlook secret iCal address, …
ev calendar fetch  <project>                         # → <project>/calendar/events.json
ev calendar blocks <project> --days 400 --past 60    # → <project>/calendar/study-blocks.json + outline
```
* **The feed URL is a secret** (it contains an access token that grants read access to the calendar). It is stored only in
  `~/.config/explainer-video/calendar.json` (permissions 600). Never print it in full, paste it into project files, commit it, or send it anywhere else.
  The project's `calendar/` folder is git-ignored; keep it that way.
* A block = consecutive sessions of the same course (split when there are more than `--gap` days between them). Titles like
  `Course - Teacher (CODE)` are split into course / teacher / code; `Block N` markers are honoured when present.
* Calendar events usually carry **no content description**, only a course link: the topic must come from the next step.

## 1b. No calendar feed? Use the course outline
Many courses live only on the learning platform. Then the **course outline is the source of truth**: ask the learner for the course page
(scan it as in step 2) or for an exported outline – a Google Doc, PDF or `.docx` with blocks, reading assignments, tasks and self-tests.
A `.gdoc`/`.gsheet` file from Google Drive for desktop is only a pointer: `ev ingest` lists its `doc_id` – read it with the Google Docs/Drive connector
(or ask for an export). Build `preparation.json` from it exactly as in step 2, and note the learner's *status* per task when the outline has it
(done / open / score) – open tasks and failed self-tests decide what to produce first.

## 2. Find the topic and the preparation per block (scan, don't guess)
For each block (start with the nearest one):
1. **Open the block's link in the browser** (built-in browser skill, or Claude in Chrome). These are usually learning-platform pages behind a login:
   * If a login page appears, **stop and ask the learner to sign in themselves** in the browser pane. Never type passwords, tokens or MFA codes for them.
   * Do not click anything that changes data (submit, enrol, post, delete). Read-only.
2. **Read** what the platform shows: course structure/modules, the schedule per session, reading lists, "preparation"/"Vorbereitung" tasks,
   files and links (PDFs, slides, literature), assignments with due dates. Use `get_page_text` / `read_page`; follow the course's own folders/pages one level deep.
3. **Download nothing without asking.** List files (name, size, source) and ask before downloading; the learner can also drop files into the project folder.
4. Write `preparation.json` (per block): `topic`, `sessions[{date, topic}]`, `must_read[{title, where, pages}]`, `tasks[{what, due}]`, `files[]`, `notes`.
   Mark anything you could not verify as `"unverified": true` and ask.

## 3. Combine with everything the learner is willing to share
Ask: *"What else can I use for this block?"* and `ev ingest` it all into one inventory:
books and slides (PDF/PPTX/DOCX), **images** (photos of whiteboards or book pages – describe/read them with vision),
**voice-note transcripts** (`.txt`/`.vtt`/`.srt`, or transcribe audio with whisper), **emails** (`.eml`, or search the mailbox with an email connector for the course name,
teacher or code), notes and web pages. Everything shared is the learner's choice; summarise what you used per block so they can veto sources.

## 4. Map sources → blocks → videos
* For each block build a short **brief**: what is taught (calendar + platform), what must be prepared (must_read), which sources cover it (with page ranges).
* Order videos by block date. Each video gets `block` (`{id, first_session}`) and `ready_by` (a date *before* the first session; default: 2 days before).
  `ev plan` flags videos that would be ready too late.
* Prefer one prep video per block ("what to read and why, the key ideas") and, where the sources are dense, extra concept videos.
* Respect time: a block 3 days away gets a short overview first, the deep dive later.

## Privacy checklist
* calendar URL, learning-platform content, emails and voice notes are **personal data**: keep them inside the learner's project folder, never in a public repo or in published sites.
* The published study site and public videos must not contain the learner's schedule, teacher names or private emails unless they explicitly agree.
