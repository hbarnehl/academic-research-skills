# GUI design (draft, 2026-11-06)

A local app for browsing literature review projects. Claude Code does the research and writes
files. The GUI reads those files and records a few decisions of yours. Clickable mockup with
fictional data: [gui-sketch.html](gui-sketch.html).

## Principles

1. **Files are the source of truth.** The GUI is a view over a project folder, not a database
   with its own state. Anything Claude writes shows up after a reload. Anything you decide in the
   GUI (override a screening decision, mark a PDF as added, add a note) is written back to the
   same files, so the next Claude session sees it.
2. **The GUI does not call the LLM (at first).** Starting a new round happens in Claude Code. The
   GUI can prepare the request (e.g. "deepen: shutdown duration") and copy the prompt or write a
   request file. Running `claude -p` from the GUI is a later option, not v1.
3. **Provenance is always visible.** Every claim about a source shows whether it rests on the
   abstract or the full text, and every weakness shows whether the authors acknowledge it or we
   infer it.

## Screens

| Screen | What you see | What you can do |
|---|---|---|
| **Projects** | One card per review: question, number of rounds, counts (included / excluded / full text), last update | Open a project, create one (writes `project.yaml`) |
| **Sources** (project tab) | Table of every source the project has touched: status, text availability, design, contribution, summary, number of weaknesses, round it entered | Filter by status, round, text availability, design; search; click a row for the detail drawer |
| **Source drawer** | Abstract, summary, key findings, evidence profile, weaknesses (with provenance and page locator), screening history per round with reasons, reports that cite it, PDF link | Override include/exclude (with a reason), add a note, open the PDF |
| **Reports** (project tab) | One version per round: R0 initial overview, R1 focus X, R2 focus Y. Reader with table of contents; citations open the source drawer | Switch versions, see which sources are new in this round |
| **Rounds** (project tab) | Timeline of rounds: focus, parent round, search strings, and a funnel (retrieved, screened on abstract, shortlisted, full text obtained, included) | Draft the next round's focus and copy the prompt |
| **Full-text queue** (project tab) | Shortlisted sources with no PDF yet | Copy the refs-fetch command for all of them, drop a PDF onto a row, mark one as "not obtainable" |

Text availability uses one icon everywhere: empty circle = metadata only, half circle = abstract,
full circle = full text read.

## Data on disk (proposal)

One folder per review project. Not inside this repo: PDFs are copyrighted and the reviews belong
to your papers. Default root to be decided (see open questions).

```
<reviews-root>/<project-slug>/
  project.yaml            title, research question, scope, created, list of rounds
  sources/<bibkey>.yaml   one file per source (see below)
  rounds/
    r0-initial/
      round.yaml          focus, parent round, search strings, date, funnel counts
      report.md           the report for this round
    r1-duration/
      ...
  pdfs/<bibkey>.pdf
  text/<bibkey>.md        converted full text
```

One file per source keeps git diffs readable and lets parallel agents write without conflicts.

Fields in `sources/<bibkey>.yaml`:

- **Identity:** `key` (BibTeX key, matches Zotero/Better BibTeX), `doi`, `openalex_id`, `zotero_key`, title, authors, year, venue
- **Text:** `abstract`, `text_status` (`none` | `abstract` | `full_text`), `pdf`, `text`
- **Screening:** a list with one entry per round: `round`, `stage` (`abstract` | `full_text`), `decision` (`include` | `exclude` | `maybe`), `reason`, `by` (`claude` | `user`)
- **Evidence profile (political science):** `design` (experiment, natural experiment, DiD, RD, IV, selection on observables, descriptive quantitative, qualitative/case study, formal theory, review), `identification` (one line), `data`, `unit_of_analysis`, `cases` (countries/regions), `period`, `contribution` (theory, measurement, causal estimate, descriptive, review)
- **Content:** `summary`, `findings` (list), `mechanism` (if any), `themes` (list)
- **Weaknesses:** list of `{text, provenance: author_acknowledged | reader_inferred, locator}`; empty unless `text_status` is `full_text`
- **Notes:** your own notes, never touched by Claude

## Tech (recommendation)

**FastAPI + Jinja templates + htmx**, served on localhost. All Python, no JavaScript build step,
easy for you to read and change. Tables, filters, drawers and a Markdown report reader are all
straightforward this way. Streamlit would be faster to start but fights you on drawers, linked
citations and custom layouts. A React frontend would be overkill for a single-user local tool.

## Decisions (2026-11-06)

1. **Where projects live:** project state outside the vault (e.g. `~/research/lit-reviews/<slug>/`,
   private git repo); paper summaries and reports in the Obsidian vault. Details in
   [obsidian-integration.md](obsidian-integration.md). The data layout above changes accordingly:
   `rounds/<id>/report.md` becomes a pointer to the vault chapter note, and `sources/<bibkey>.yaml`
   caches fields derived from `readings/<bibkey>.md` with a hash for staleness checks.
2. **Later rounds** write a chapter of one combined report, not a new version. See
   [workflow.md](workflow.md).
3. **Inclusion is per round.** The status column shows the selected round's status; the
   all-rounds view shows which rounds include the source.

## Open questions

1. **Rounds as a line or a tree?** The data model allows branching (R2 building on R0). Does the
   GUI need to draw it, or is a "builds on" label enough?
2. **Zotero sync direction.** Should included sources be added to a Zotero collection per project
   automatically (refs-fetch already talks to Zotero), or only on request?
3. **Vault staleness in the GUI.** How loud should "vault note changed since extraction" be: a badge
   per source, or a banner listing all stale sources with one re-derive button?
