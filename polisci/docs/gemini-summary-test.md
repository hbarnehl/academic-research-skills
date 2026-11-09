# Test: are the Gemini summaries good enough? (2026-11-09)

Five literature notes with Gemini summaries (`read_paper.py`, paper template) were checked
against the full PDF text by Claude. The papers are central to Paper 2 and vary in design.

| Paper | Design |
|---|---|
| Gohdes (2020), AJPS | Subnational panel, Syria, binomial GLM |
| Shapiro & Weidmann (2015), IO | District first differences + tower-level DiD, Iraq |
| Pierskalla & Hollenbach (2013), APSR | Grid cross-section + IV + panel, Africa |
| Weidmann (2016), AJPS | Measurement: media vs military records, Monte Carlo, diagnostic |
| Lyall (2009), JCR | Natural experiment (H&I artillery fire), matching + DiD, Chechnya |

## Bottom line

**Good enough for orientation and full-text screening, not good enough as the basis for the
evidence profile or for focused rounds.**

- **Reliable:** research question, theory, hypotheses, data sources, units, period, sample sizes
  and headline numbers. All ~29 numbers checked were correct, for example: 14 governorates and
  640 obs; 2,416 towers and −0.896 attacks per period (~40%); 9,343 cells and +0.5 to 3 pp on a
  1% baseline; reporting probability 0.216 → 0.275; 159 matched pairs and −24.2%.
- **Unreliable:** the Discussion section and anything about identification or measurement.

## Problems found

| Problem | Papers affected | Examples |
|---|---|---|
| **Invented or misattributed limitations and extensions** | 3 of 5 | Gohdes: "difficulty of accounting for unreported killings" listed as an acknowledged limitation; the paper treats it as solved by multiple recapture. Shapiro & Weidmann: SIM regulation and urban terrain presented as "future research"; in the paper they are policy relevance and literatures spoken to. Weidmann: "the diagnostic should be a standard requirement" and "apply it to road accessibility" appear nowhere in the paper. (Corrected 2026-11-09: the SIGACTS-gaps limitation is real, p. 211.) |
| **Hedges flattened into stronger claims** | 3 of 5 | Weidmann: "primarily driven by reporting bias"; the paper says "partly" and "cannot conclusively refute". Pierskalla & Hollenbach: "IV models confirm this is not merely endogenous network expansion". Gohdes: Alawi-area relationship "is negative"; the paper says "if anything, negative". |
| **Identification missing or thin** | 3 of 5 | Gohdes: no mention that there are time fixed effects but no governorate fixed effects, only 14 clusters, and that intentional access restriction is an assumption. Shapiro & Weidmann: the identifying assumption (month-to-month tower timing driven by logistics such as land titles, placebo tests, first differences because of district trends) is reduced to "spatial-temporal DiD". Pierskalla & Hollenbach: the instrument is a country-level score (CPIA 2005–07) for a 55 km cell-level treatment, and the exclusion-restriction argument is not given. |
| **Measurement details missing** | 3 of 5 | Gohdes: targeted killings are mostly classified by *method of killing* (xgboost, 2,347 hand-coded records); the summary only says "e.g. snipers". Shapiro & Weidmann: the DV excludes attacks on civilians. Lyall: the event data come from ~20 media, human-rights and press-release sources, a reporting concern the summary does not surface. |
| **Points most relevant to Paper 2 dropped** | 3 of 3 where relevant | Shapiro & Weidmann's argument that cellphone coverage raises the *reporting* of violence, so measurement error correlates with the treatment. Gohdes's note that Internet access may affect the ability to report. Pierskalla & Hollenbach's argument for why reporting bias is unlikely in their data. All three bear directly on observability in Paper 2; none appears in the summaries. |
| **Small factual errors** | 3 of 5 | Shapiro & Weidmann: direct-fire attacks described as significantly reduced (not significant at the district level). Lyall: property damage described as negatively correlated (it is the one measure that is not). Gohdes: H2 reported as "supported", though the proportion model cannot test it separately from H1. |
| **No page locators** | 5 of 5 | The template asks for none, so no claim can be checked quickly. |

Lyall (2009) came out best: accurate, with correct limitations (90-day windows, the war-crimes
caveat). Gohdes and Shapiro & Weidmann came out worst on what Paper 2 would need.

## What this means for the design

1. **Keep the Gemini summary as the general layer**, for orientation and full-text screening. It
   gets the what-and-where right.
2. **Do not derive the evidence profile or weaknesses from it.** These come from a separate pass
   over the full text: identification strategy and its assumption, fixed effects and clustering,
   measurement of the DV and IV, and weaknesses with provenance. This is the project-specific
   pass, with page locators.
3. **Treat its Limitations and Extensions sections as unreliable** until the template is fixed.
4. **Template changes for `read_paper.py`**, by mode. The script has several templates: Mode A
   (empirical/theoretical paper), Mode B (review paper), Modes C1 to C3 (methods papers, `--methods`)
   and the book templates. The changes must respect that not every paper has measurement or results.

   **Rules for all modes** (added to the shared "Critical Rules"):
   - Limitations, extensions, research gaps and avenues: only what the authors state, quoted
     briefly with a page number; otherwise *Not discussed in text*. This also covers Mode B's
     "research gaps and avenues" and the methods templates.
   - Keep the authors' hedging verbatim ("partly", "if anything", "suggests").
   - Page numbers for hypotheses or propositions, main results and limitations.

   **Mode A only, split by paper type.** Mode A currently lumps empirical and theoretical papers
   together. In the vault, conceptual papers are forced into the empirical slots: Kalyvas (2003)
   gets a "Dependent variable", "Estimation: qualitative process tracing" and "Controls: Not
   discussed in text". Adding more empirical fields would make this worse. So:
   - Classification step distinguishes **A1 empirical** (quantitative or qualitative evidence) from
     **A2 theoretical** (formal model or verbal/conceptual theory), keeping the same six headings
     so existing notes stay uniform.
   - A1: two new bullets inside `## Methodology` (no new headings). **Identification**: strategy,
     identifying assumption in the authors' words, fixed effects, clustering and number of
     clusters, threats the authors discuss. **Measurement**: how the DV and key IV are produced
     (data-generating process, classification, reporting source) and the biases the authors
     discuss. Results get effect sizes with units.
   - A2: `## Methodology` describes the formal setup (players, strategies, solution concept, key
     assumptions) or the conceptual approach. `## Results` lists propositions and comparative
     statics, or the main conceptual claims. Empirical bullets are written as *Not applicable
     (theoretical paper)*, not *Not discussed in text*, so a missing field is not mistaken for an
     omission by the authors.
   - Qualitative empirical papers (case studies, process tracing) are A1. Their identification
     bullet covers case selection and the logic of inference instead of fixed effects and clustering.

   **Mode B and the methods modes:** no new sections. Mode B has no identification or results to
   report. C1 already covers identification and C2 measurement. Only the rules for all modes apply.

   **Re-run.** The same five papers, plus one theoretical paper (Kalyvas 2003, conceptual) and one
   review (Gehlbach, Sonin & Svolik 2016, the only vault note in Mode B, so before and after can be
   compared), so the changes are checked for regressions in the other modes. Gemini Flash may simply be
   weaker at the judgement-heavy parts; if so, use a stronger model for this template only.

## Re-run with the revised template (2026-11-09)

Template changes as proposed above, on branch `template-v2` of `paper-reader`, same model
(`gemini-3.8-flash`). Run on scratch copies of the five notes plus Kalyvas (2003, conceptual) and
Gehlbach, Sonin & Svolik (2016, review); the vault notes were not touched.

**Mechanical check of quotes and pages.** A script looked up every quoted passage in the PDF
text and compared the page it is on with the cited page (journal pagination).
- 66 quotes across the seven summaries: all 66 exist in the papers. Three needed a looser match
  because of hyphenation at line breaks.
- All cited pages are correct.

**Against the problems from the first run:**

| Problem (first run) | Re-run |
|---|---|
| Invented or misattributed limitations and extensions | None found. Limitations and extensions are now quotes from the paper. Gohdes's "extensions" partly quote implications rather than research suggestions, but nothing is invented. |
| Hedges flattened | Fixed in the checked cases. Gohdes: Alawi areas "slightly negative, statistically indistinguishable". Weidmann quotes "cannot conclusively refute". |
| Identification thin | Much better. Shapiro & Weidmann: identifying assumption quoted (p. 257), 63 and 1,859 clusters, threats and responses. Pierskalla & Hollenbach: IV assumption with the national-level CPIA score. Lyall: H&I doctrine at Shali (71%) and inebriation or accidents at Khankala (29%). Gohdes still does not say outright that there are no governorate fixed effects, but the fixed effects that are included are listed. |
| Measurement details missing | Fixed. Gohdes: xgboost, 2,347 hand-coded records, multiple recapture. Shapiro & Weidmann: DV excludes attacks on civilians. Lyall: more than 35 sources for attacks. |
| Points most relevant to Paper 2 dropped | Fixed in all three. Gohdes: reporting and network access confounding, addressed by multiple recapture. Shapiro & Weidmann: military logs chosen to avoid media reporting bias. Pierskalla & Hollenbach: how they handle reporting bias in remote areas. |
| Small factual errors | The Lyall property-damage and Shapiro & Weidmann direct-fire errors are corrected. Remaining: Gohdes H2 still "supported" without noting that it is not tested separately from H1, although the template now asks for this. |
| No page locators | Fixed: pages on hypotheses, results, limitations and most other claims. |

**Other paper types.**
- Kalyvas is classified as theoretical. Methodology gives the conceptual setup, Results gives the
  main conceptual claims, and all empirical fields read "Not applicable (theoretical paper)"
  instead of the forced DV/IV of the old note.
- Gehlbach et al. is classified as a review. The conclusion now quotes the authors' gaps and
  avenues with pages, and is more specific than the old version.

**Costs.**
- Summaries are 1.4 to 2.6 times longer (1,250 to 2,400 words instead of 860 to 1,140).
- Each run took about one to three minutes.

**Verdict.** The revised template is good enough for the general layer, and its Identification
and Measurement bullets can feed a draft evidence profile. The draft still needs a check in the
project pass, since judgement calls such as "H2 tested separately?" can still slip.

## Caveat

Claude made these judgements against the PDF text; they were not double-checked by a person. The
first write-up contained two false accusations (a real Coalition-battalions control and a real
SIGACTS limitation were called invented, because a text search used different wording). Both are
corrected above. The quote and page check in the re-run is mechanical; the substantive checks are
spot checks.
