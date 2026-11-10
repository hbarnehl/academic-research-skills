# Political-science literature review (fork of ARS)

This repo is a fork of [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) (ARS).
Our own work is an iterative literature review workflow for political science, with a local GUI.
It lives entirely in `polisci/`. Everything else is upstream ARS.

- `origin`: git@github.com:hbarnehl/academic-research-skills.git (our fork)
- `upstream`: git@github.com:Imbad0202/academic-research-skills.git

`.claude/CLAUDE.md` is upstream's maintainer guide. It applies when reading or reusing upstream
files, not to how we build things in `polisci/`.

## Goals

1. **Political-science framework.** Grade sources by research design and identification
   (experiment, natural experiment, DiD/RD/IV, selection on observables, descriptive,
   qualitative, formal theory) and by contribution type, instead of ARS's medical evidence
   pyramid (`deep-research/references/source_quality_hierarchy.md`). Gaps are framed as
   mechanisms, scope conditions, cases/regions, measurement and identification.
2. **Abstract first, then full text.** Screen candidates from abstracts (OpenAlex, Semantic
   Scholar), let the user approve a shortlist, fetch PDFs with refs-fetch
   (`~/personal_projects/refs-fetch`) or let the user drop them in, convert to text, then read
   the full papers. Every source records what was read (abstract only / full text).
3. **Iterative.** A review is a project with rounds: an initial report, then rounds that
   deepen one subfield. Each round builds on the stored corpus, screening decisions and earlier
   reports rather than starting over. All report versions are kept.
4. **GUI.** A local app to browse projects, sources (included/excluded, abstract/full-text
   status, evidence profile, weaknesses) and report versions. See `polisci/docs/gui-design.md`.

## Ground rules

- **Additive only.** Do not edit upstream ARS files. Reuse them by reference (verification
  protocols, Zotero adapter in `scripts/adapters/`, synthesis approach, `/ars-mark-read`
  read-scope tracking). If an upstream file truly must change, say so first and keep the change
  minimal so `git merge upstream/main` stays clean. Upstream moves fast (~50 commits/month).
- **Files are the source of truth.** Review projects are plain files (YAML/JSON + Markdown) that
  Claude Code writes and the GUI reads. The GUI never holds state of its own.
- **Never fabricate sources.** Every source must resolve in OpenAlex, Semantic Scholar or
  Crossref, and claims about a paper's content must say whether they rest on the abstract or the
  full text.
- Python: uv, project env only. Keep code clear and idiomatic rather than clever.
- Prose in reports: British spelling, no em dashes, dense academic style. Citations as BibTeX
  keys so they work with `\parencite`.

## Layout

```
polisci/
  docs/          plans, design notes, GUI sketch (start with docs/README.md)
  scripts/       prototype pipeline scripts (Gemini abstract screening, library embedding index,
                 OpenAlex citation chasing and keyword search, cluster map, appraisal quote check
                 and compilation)
  prompts/       prompts for subagents (critical appraisal)
```

Add new top-level folders under `polisci/` to this list as they are created (skill, app, etc.).

## Syncing with upstream

```
git fetch upstream
git merge upstream/main
```
