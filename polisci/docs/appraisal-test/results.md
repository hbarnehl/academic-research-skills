# Appraisal test: results (2026-11-09)

Which model should write the critical appraisal (stage 5)? Gemini 3.8 Flash, Sonnet and Opus each
appraised three recent, little-cited papers, using the same prompt and the PDF as input. The
outputs were rated blind (labels shuffled per paper).

## Unblinded preferences

| Paper | Preferred | A / B / C were |
|---|---|---|
| Talgatova (2026) | A = **Sonnet** | Sonnet / Opus / Gemini |
| Tierney et al. (2025) | B = **Opus** | Gemini / Opus / Sonnet |
| Shirikov (2024) | A / C tied = **Sonnet and Opus** | Sonnet / Gemini / Opus |

Gemini was never preferred. Sonnet and Opus each won one paper and tied on the third.

## Supporting numbers

| | Gemini Flash | Sonnet | Opus |
|---|---|---|---|
| Weaknesses (3 papers) | 27 | 30 | 30 |
| Reader-inferred / author-acknowledged | 12 / 15 | 18 / 12 | 17 / 13 |
| Marked high severity | 8 | 11 | 10 |
| Quotes real and pages correct | all | all | all |
| Cost | ~1 min per paper, Gemini API | ~95k tokens per paper, Pro usage | ~95k tokens per paper, Pro usage |

Gemini leans on limitations the authors already state. Its share of reader-inferred weaknesses
is the lowest, and those are the part an appraisal exists for. Quote accuracy does not separate
the models: all 89 quotes were verbatim and correctly paged.

Only 9 individual weaknesses were rated (all `v`, all from Sonnet's Talgatova appraisal), so
there is no precision score per model.

## Decision

- **Stage 5 (critical appraisal): Sonnet subagents.** Sonnet matched Opus on preference at lower
  weight on Pro limits. Gemini Flash is not used for appraisal.
- **Keep the token cost down:** about 95k tokens per paper came from reading the whole PDF. In the
  pipeline, the appraisal reads only the sections the v2 summary points to (design,
  identification, results, robustness), which should cut this substantially. That is untested.
- **Gemini stays for extraction work:** v2 summaries, full-text screening, and probably focused
  reading notes. Focused notes are extraction rather than judgement, but this has not been tested.

## Limits of this test

Three papers, one rater, preferences rather than item-level ratings. That is enough to rule out
Gemini Flash for appraisal, but not to rank Sonnet against Opus. If appraisals turn out weak in
practice, re-test Opus on a larger set.
