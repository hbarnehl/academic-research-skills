# Obsidian integration (proposal, 2026-11-06)

How the literature review workflow fits with the PhD vault (`~/obsidian/phd`), its literature
notes (`readings/<citekey>.md`) and the Gemini summary script.

## What already exists in the vault

- **717 literature notes** in `readings/`, filename = Better BibTeX citekey, created by the Zotero
  Integration plugin. Only the region between `%% begin notes %%` and `%% end notes %%` survives a
  re-import; frontmatter, info/abstract callouts and the annotation list are regenerated.
- **169 of them have a structured full-text summary** written into the notes block by
  `read_paper.py` (Gemini, launched from Obsidian via QuickAdd `user_scripts/run-read-workflow.js`;
  repo `~/personal_projects/paper-reader`, private `hbarnehl/paper-reader`). Its paper template has fixed headings: Introduction,
  Extant Literature, Theory, Methodology (design, data, unit, coverage, DV/IV, estimation,
  robustness), Results, Discussion (including acknowledged limitations).
- **Zotero highlights by colour**, including `!` weaknesses and `€` hypotheses. These are the
  user's own reading signal.
- Conventions: machine-written notes get `generated-by: claude`; research reports are named
  `<model> report on <topic>`; readings are cited as `[[citekey|Author (Year) Short Title]]`.

## Core idea: split ownership, derive one way

The risk of integrating is two copies of the same information drifting apart. The answer is
to give every piece of information exactly one owner.

| Information | Owner | Why |
|---|---|---|
| What a paper says (summary, design, data, findings, acknowledged limitations) | **Vault**, `readings/<citekey>.md` notes block | It is knowledge about the paper, not about one review. Reused across projects and papers. |
| Your own reading signal (highlights, own notes) | **Vault** (Zotero + notes block) | Already yours; the review only reads it. |
| Reports (one note per round, see `workflow.md`) | **Vault**, as `claude report on <topic>` notes | You read, annotate and link them like any other note. Citations become working `[[citekey]]` links. |
| Review-specific judgements: candidates, screening decisions per round, relevance to this question, search strings, funnel counts | **Review project folder** (outside the vault) | Machine state, mostly about papers you will never import. Hundreds of excluded candidates should not become vault notes. |
| Structured fields the GUI needs (design, identification, contribution, weaknesses) | **Review project folder, as a cache derived from the vault note** | See below. |

**One-way derivation with staleness checks.** The review project never stores its own version
of a paper's content. It derives structured fields from the vault note and records a hash of the
notes block it read. If you later edit that note in Obsidian, the hash no longer matches and the
GUI shows "vault note changed since extraction" with a button to re-derive. Your edit always wins.
Nothing in the vault is ever overwritten from the review side.

**What Claude may write in the vault.**
- Into an existing literature note: only inside the notes block, only when the block has no
  summary yet, and in the same template as `read_paper.py` so the vault stays uniform. Never
  over an existing summary or your own notes.
- New report notes, marked `generated-by: claude`. After creation they are yours: the next round
  reads the current file, including your edits.

## Two kinds of summary: general (vault) and focused (per round)

A general summary will often be too coarse for a round that focuses on a detail. But a
focused extraction should not replace the general summary either. So there are two layers,
both read from the same full text:

| | General summary | Focused reading notes |
|---|---|---|
| Question | What does this paper do and find? | What does this paper say about *this round's focus*? |
| Written | Once per paper | Once per paper per round that needs it |
| Lives in | Vault, notes block of `readings/<citekey>.md` (Gemini template) | Review project, e.g. `rounds/r1-duration/reading-notes/<citekey>.md` |
| Content | Fixed template: RQ, theory, design, data, results, acknowledged limitations | Only what bears on the focus: relevant passages, quotes with page numbers, how the paper measures or handles the focus variable, weaknesses relevant to the focus |
| Used for | Full-text screening, the evidence profile, orientation | Writing the round's chapter; every claim in the chapter cites a page |

Nothing is overwritten: a focused round adds reading notes next to the general summary. The
GUI's source drawer shows the general summary plus one tab per round with reading notes.

**How ARS does it, for comparison.** ARS has no persistent per-paper summary. In each run the
bibliography agent writes an annotated-bibliography entry per source, aimed at that run's
question: relevance, key findings, method, quality, and method weaknesses. Each weakness is labelled
author-acknowledged or reader-inferred, and method critique is banned if only the abstract was
read. Citations in the synthesis carry quote or page anchors. That is essentially our focused
layer, rebuilt from scratch every run, without the reusable general layer.

**Is the Gemini summary good enough?** Tested in two rounds
([gemini-summary-test.md](gemini-summary-test.md)). The first template got numbers and structure
right but invented limitations, flattened hedges and skipped identification and measurement. The
revised template (v2, live since 2026-11-09) fixed most of this. Every quote and page checked
out, identification and measurement are covered, and limitations are quoted from the paper.
Judgement calls can still slip (Gohdes's H2 still "supported" although it is not tested
separately).

## What each source gets, by stage (after template v2)

The Gemini summary now carries more weight than planned, but it does not replace reading the
full text. It replaces reading it *blind*: Claude reads targeted sections with the summary as a
map, instead of the whole paper.

| Stage | Applies to | Based on | Output |
|---|---|---|---|
| 1. Abstract screening | All candidates (often hundreds, from search and citation chasing) | OpenAlex / Semantic Scholar abstract | Shortlist |
| 2. Get the full text | Shortlist | refs-fetch, Zotero import, `read_paper.py` v2 | Vault note with v2 summary |
| 3. Full-text screening | Shortlist | v2 summary | Include / exclude for this round, with reason |
| 4. Evidence profile (draft) | Included | Parsed from the v2 summary: paper type, design, identification, measurement, data, unit, cases, period. Quotes and pages checked mechanically | `sources/<key>.yaml` |
| 5. Critical appraisal | Included | **Full text**, targeted: design, identification, results and robustness sections, located via the summary. **Sonnet subagent** (tested against Gemini Flash and Opus, see [appraisal-test/results.md](appraisal-test/results.md)) | Reader-inferred weaknesses with pages; corrections to the draft profile |
| 6. Focused reading notes | Included sources the round's focus touches | **Full text**, searched for passages on the focus | `rounds/<id>/reading-notes/<key>.md` with quotes and pages |
| 7. Chapter | The round | Reading notes, appraisal, summaries | Chapter note; every claim about a paper cites a page |

Why full text is still needed at stages 5 and 6:
- **Weaknesses:** the template deliberately reports only what the authors state. Weaknesses the
  authors do not acknowledge (e.g. no unit fixed effects, 14 clusters, H2 not separately testable)
  need a critical read, and these are exactly the judgement calls Gemini still gets wrong.
- **Focus:** a general summary cannot anticipate every round's focus. A round on shutdown
  measurement needs the paper's measurement details and caveats in full, with pages.

**Old v1 summaries (about 169 notes).** For included sources whose note has a v1 summary,
stage 2 re-runs v2. That is only safe if the notes block holds nothing but the Gemini summary.
If you have written your own notes in the block, the v2 summary goes into the review project
instead of the vault, and you decide whether to merge it.

**Cost.** Stage 3 costs one Gemini Flash call per shortlisted paper. Stages 5 and 6 are the
expensive Claude reads, done only for included papers, and only on the sections that matter.

## Full-text stage, with the vault in the loop

Many papers are in Zotero but have no vault note, so the vault cannot be assumed. Stage 2 above,
for each shortlisted source:

1. **No Zotero item?** refs-fetch adds it by DOI and fetches the PDF through UCSD access.
2. **Zotero item but no PDF?** refs-fetch (`refs-missing`, Chrome download, `refs-attach`).
3. **No vault note?** Import it automatically (see below).
4. **Vault note without a v2 summary?** Run `read_paper.py` on it (see the v1 caveat above).

### Automatic import into the vault

The Zotero Integration plugin has a function that imports one citekey without the picker
dialog: `app.plugins.plugins["obsidian-zotero-desktop-connector"].runImport("import paper", "<citekey>")`
(`"Import book"` for books). It renders the usual template, so the note is identical to a manual
import. It needs Obsidian and Zotero running. Ways to trigger it from outside Obsidian:

- **Queue file plus one QuickAdd command (recommended first step).** The pipeline writes the
  citekeys to import into a queue file. A QuickAdd user script (like `run-read-workflow.js`) reads
  the queue, calls `runImport` for each, and optionally runs `read_paper.py` on each new note.
  One command imports and summarises a whole batch.
- **Obsidian CLI** (`obsidian eval`, Obsidian 1.12+). Fully automatic. It is not on PATH on this
  machine yet (Obsidian 1.15 AppImage; the CLI is enabled in Obsidian's settings), and the vault's
  rules ask for approval for each `eval`.

## Where the review project folder lives

Outside the vault, e.g. `~/research/lit-reviews/<slug>/` as a private git repo, so it syncs
across your machines like `~/.claude` does. Obsidian Sync is the alternative but is not built for
YAML state files. The vault only holds the human-facing outputs.

## Open points

1. Gemini or Claude for the summary step? Gemini Flash is cheap and already trusted. Using
   Claude would put everything on one provider, but costs more.
2. Queue-file QuickAdd command or Obsidian CLI for the automatic import? The first works now;
   the second needs the CLI enabled and an approval rule for `eval`.
3. Should round reports link back to the project (a hub note per review in `notes/`), following
   the vault's project-note conventions?
