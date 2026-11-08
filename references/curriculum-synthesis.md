# Curriculum synthesis (Step 2) – from “a pile of data” to a personal course

Input: a folder of source material (PDFs, Word, slides, notes, web pages saved as HTML/Markdown) **and** `learner-profile.json`.
Output: `curriculum.json` + a reviewed plan, then one project per video (`ev plan --scaffold`).

## 1. Ingest
`ev ingest <folder> --out <project>` → `sources/*.txt` (page-marked text) + `sources/inventory.json` (per file: type, pages, words,
detected headings, rough reading time). Skim the inventory first: what is theory, what are exercises, what is duplicate, what is out of scope?
Scanned PDFs have noisy text – read figure captions, rebuild diagrams from the prose.

## 2. Topic map
Read the sources and build, in your own words: the list of **concepts** (with the page range where each is explained), their
**prerequisites** (a small dependency graph) and the **learner-relevant weight** (exam relevance, job relevance, prior knowledge).
Flag gaps and contradictions between sources. Ask the learner to confirm anything ambiguous – never invent facts.

## 3. Prune and sequence (this is where personalisation matters)
* Cut or compress what the profile says they already know (`prior_knowledge`) or do not need (`goal`).
* Order by prerequisites first, then by the learner’s style: *examples-first* learners get “case → concept → rule”; *rules-first* learners get the reverse.
* Respect `deadline` and `session_minutes`: number of videos = relevant content ÷ chars-per-minute × target length (`ev plan` computes it).
* One idea per scene, 30–70 s; 6–9 scenes per video; each video ends with a recap and opens with a 10-second retrieval question about the previous one.

## 4. Chunk into videos
Group concepts into videos of the target length. For every video write (this goes into `curriculum.json`):
`slug`, `title`, `objectives` (3 verbs: “explain…”, “apply…”), `source_refs` (file + pages), `concepts`, `analogy` (domain from the profile winners/likes, and *why it fits*),
`example` (from the running example), `mnemonic` (style from the profile), `quiz` (3–5 Q/A), `est_minutes`.

## 5. Review gate (before any narration credits are spent)
Show the learner the outline: modules → videos → one-line promise each, total time, what was cut and why. Let them re-order, merge, drop.
Only then continue.

## 6. Produce
For each video: storyboard (scenes ↔ takeaways) → `script.md` in the profile’s tone → `scenes/*.html` (use `scene_kit.py`:
`example_scene` for analogy/example/mnemonic, `bridge_scene` for “where are we”, `recap_scene`) → `ev preview` → `ev shots` → `ev narrate --dry-run` → `ev all` → `ev site`.
After the first video ask: “Which analogy landed? Which felt forced?” and update the profile.

## `curriculum.json`
```json
{
  "title": "Systems Engineering in 5 videos", "language": "de", "profile": "learner-profile.json",
  "sources": ["sources/inventory.json"],
  "modules": [{
    "id": "m1", "title": "Thinking in systems",
    "videos": [{
      "slug": "t1", "title": "Teil 1: Elemente und Beziehungen",
      "objectives": ["explain what an aspect of a system is", "apply it to a case"],
      "source_refs": [{"file": "book.pdf", "pages": "130-136"}],
      "concepts": ["Element", "Beziehung", "Aspekt"],
      "analogy": {"domain": "cooking", "idea": "same ingredients, different recipes = different aspects"},
      "example": "running case: online shop",
      "mnemonic": "E × B = Aspekt",
      "quiz": [{"q": "What is an aspect?", "a": "A combination of an element category with a relation category."}],
      "est_minutes": 8
    }]
  }]
}
```
Faithfulness rules: keep the source’s terms and numbers; label your own examples as yours; cite pages in script notes (`> p. 138: …`);
paraphrase, never copy long passages.
