# Review workflow: projects and rounds (draft, 2026-11-06)

Nothing here is implemented yet. This records the decisions so far.

## A project is a sequence of rounds

- **R0, the overview**, maps the literature on the project's question.
- **Each later round has a focus** (e.g. "shutdown duration", "measuring shutdowns") and names
  the round it builds on. Usually that is the previous round, but a round can branch from an
  earlier one.

## Reports are chapters, not versions

Each round writes **one chapter** of a combined report:

- A chapter assumes the earlier chapters it builds on and does not repeat them. It refers back
  to them where needed ("as in Chapter 1, …").
- A chapter stands on its own as an argument about its focus.
- A short **report hub** (introduction plus a table of contents linking the chapters) is
  regenerated after each round. It is the only text that changes when a new chapter is added.

In the vault: one hub note `claude report on <topic>` and one note per chapter, so each chapter
can be read, edited and linked separately (see `obsidian-integration.md`).

## Inclusion is per round

A source can be excluded for the overview but central to a deep dive. Screening decisions
are stored per round. The GUI's status column shows the status for the selected round; in the
"all rounds" view it shows which rounds include the source.

## What a round looks at: existing sources first, then new ones

A new round is not only a new search. It works through four pools in order, from highest to
lowest precision. Pools 1 and 2 follow the corpus-first, search-fills-gap flow that ARS already
has for a user corpus.

1. **Sources already in the project**, *including ones excluded in earlier rounds*, re-screened
   against the new focus. Example: a measurement paper excluded from the overview becomes central
   to a measurement round.
2. **Your own library**: the Zotero library (larger than the vault) and vault readings that never
   entered this project.
3. **Citation chasing** from the sources included so far (or from seed papers you name):
   - *Backward*: works cited by the included papers. OpenAlex `referenced_works` gives these
     without the PDF; for gaps (books, working papers), parse the reference section of the full
     text, which refs-fetch already does (Haiku parses references, then Crossref/OpenAlex DOIs).
   - *Forward*: works citing the included papers, via OpenAlex (`filter=cites:<work id>`).
     Semantic Scholar's citations endpoint adds the sentence in which each citing paper cites the
     seed, which shows at a glance whether it engages with the seed or only mentions it.
   - *Ranking*: chasing produces many candidates (dozens of references per paper, sometimes
     hundreds of citing works). Candidates linked to several included papers, cited by several or
     citing several, rank first. Then abstract screening against the round's focus as usual.
4. **A targeted keyword search** for what pools 1 to 3 do not cover. The round reports which
   sub-questions were left uncovered and why it searched.

**Pool 2 is ranked before it is screened.** The library is not screened item by item each round.
An embedding index of the library (title + abstract, `polisci/scripts/embed_library.py`) is built
once and updated as items are added; a round ranks the library by similarity to its question and
sub-strands, and only the top 150 go to abstract screening. Benchmarked on R0 of the satellite
conflict detection review (1,205 items, full Gemini screen as reference): the top 100 held all 47
includes and 61 of 64 include-or-maybe items, the top 150 held 62 of 64, the two misses weak
`maybe`s. Items without an abstract (a quarter of the library) are ranked on the title alone, which
held up in that test but is the weak spot to watch.

Every candidate records which pool and which seed paper it came from, so the GUI can show, for
example, "found by forward citation from Ferreira & Holm (2022)".

**An overview round maps from abstracts and reads only a core.** In the first trial (R0,
satellite conflict detection) the four pools produced 428 include-or-maybe sources, far more than
can be read in full. So R0 clusters the whole corpus (embeddings, k-means, Gemini names each
cluster from its central abstracts), reports funnel counts and gaps from abstracts, and picks a
core of about 30 for full text: the most-linked papers per cluster, reviews, and papers bridging
the review's strands. Later rounds deepen one cluster each. Topics that are out of scope for a
round but worth keeping get the screening decision `defer` with a topic name, so a later round
finds them in pool 1.

**Appraisal and chapter in the first trial (2026-11-10).** The 30 core papers were appraised by
Sonnet subagents with `polisci/prompts/appraisal.md`, given the v2 summary as a map and the PDF
text split by page. Lessons:
- *Cost did not fall.* About 105k to 155k tokens per paper (median about 120k), close to the
  whole-PDF cost in the model test. Most of it is the agent's fixed context re-sent on each tool
  call, not the paper text, so "read only the relevant pages" saves little on papers of 5k to 20k
  words. Fewer tool calls matter more than fewer pages.
- *Quotes are reliable, and checkable.* `polisci/scripts/check_quotes.py` matched all 220 quotes
  against the text; 2 had one word added and were corrected. Text must be extracted in reading
  order (`pdftotext` without `-layout`, which interleaves columns); the checker normalises
  ligatures, soft hyphens, control characters and the line numbers of line-numbered preprints.
- *Stage 6 (focused reading notes) was skipped for R0.* An overview has no narrow focus; the
  appraisal's "For this review" section and the v2 summaries were enough for the chapter, whose
  page citations come from the checked quotes. Focused notes start with the first deepening round.
- `polisci/scripts/compile_appraisals.py` turns the appraisals into a table of design,
  contribution and weakness counts by type and severity, which the chapter's synthesis drew on.

This allows two kinds of round:

- **Deepen**: all four pools. New material plus a re-reading of the old.
- **Re-analyse**: pools 1 and 2 only, no new search. For a different question about sources you
  already have (e.g. "compare how the included studies measure shutdowns", "which findings depend
  on media-coded data?").

A round that needs detail on its focus also writes focused reading notes per source (see
`obsidian-integration.md`, "Two kinds of summary").

The Rounds screen in the GUI shows the funnel per pool, so you can see what a round reused and
what it found.

## Status in ARS

ARS has the corpus-first flow (pools 1 and 2 in one step) for a single run, plus the Obsidian
and Zotero adapters. It does not do citation chasing: backward citation appears only as a line
in its systematic-review protocol template. It has no notion of rounds, per-round screening,
re-screening excluded sources, or chapters that build on each other. All of that is ours to build.
