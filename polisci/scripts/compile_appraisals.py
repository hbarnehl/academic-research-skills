"""Compile per-paper appraisals (prompts/appraisal.md format) into one JSON file and a Markdown table.

Usage:
    python compile_appraisals.py APPRAISAL_DIR CORE_JSON OUT_JSON OUT_MD

CORE_JSON supplies title, year and cluster for each citekey. The Markdown has one row per paper
(design, contribution, validation, weakness counts) and counts of weakness types by severity.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def field(block: str, name: str) -> str:
    m = re.search(rf"\*\*{name}\*\*:\s*(.+?)(?=\n- \*\*|\n\n|\n##|\Z)", block, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def section(text: str, title: str) -> str:
    m = re.search(rf"^## {title}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def parse(text: str) -> dict:
    profile = section(text, "Profile")
    weaknesses = []
    for title, body in re.findall(r"^### W\d+: (.+?)\n(.*?)(?=^### |^## |\Z)", text, re.S | re.M):
        typ, prov, sev = field(body, "Type"), field(body, "Provenance"), field(body, "Severity")
        weaknesses.append({
            "title": title.strip(),
            "type": re.split(r"[,;(]", typ)[0].strip().lower(),
            # an appraisal may mark one weakness as partly acknowledged and partly inferred
            "provenance": ("mixed" if "author" in prov and "reader" in prov
                           else "author" if "author" in prov else "reader"),
            "severity": (re.match(r"\w+", sev).group(0).lower() if sev else ""),
            "weakness": field(body, "Weakness"),
        })
    return {
        "main_claim": section(text, "Main claim"),
        "paper_type": field(profile, "Paper type"),
        "design": field(profile, "Design"),
        "contribution": field(profile, "Contribution"),
        "validation": field(profile, "Ground truth / validation"),
        "for_review": section(text, "For this review"),
        "weaknesses": weaknesses,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("appraisals")
    ap.add_argument("core")
    ap.add_argument("out_json")
    ap.add_argument("out_md")
    args = ap.parse_args()

    core = {c["citekey"]: c for c in json.loads(Path(args.core).read_text())}
    papers = {}
    for f in sorted(Path(args.appraisals).glob("*.md")):
        p = parse(f.read_text())
        c = core.get(f.stem, {})
        p.update(citekey=f.stem, title=c.get("title"), year=c.get("year"), cluster=c.get("cluster"))
        papers[f.stem] = p
    Path(args.out_json).write_text(json.dumps(papers, indent=1, ensure_ascii=False))

    lines = ["| Paper | Cluster | Design | Contribution | High / med / low | Reader-inferred (incl. partly) |",
             "|---|---|---|---|---|---|"]
    for p in sorted(papers.values(), key=lambda p: (str(p["cluster"]), int(p["year"] or 0))):
        sev = Counter(w["severity"] for w in p["weaknesses"])
        reader = sum(w["provenance"] != "author" for w in p["weaknesses"])
        design = re.split(r"[:.]", p["design"])[0]
        lines.append(f"| {p['citekey']} | {p['cluster']} | {design} | {p['contribution']} | "
                     f"{sev['high']} / {sev['medium']} / {sev['low']} | {reader} of {len(p['weaknesses'])} |")

    by_type = Counter((w["type"], w["severity"]) for p in papers.values() for w in p["weaknesses"])
    types = sorted({t for t, _ in by_type}, key=lambda t: -sum(by_type[(t, s)] for s in ("high", "medium", "low")))
    lines += ["", "| Weakness type | High | Medium | Low |", "|---|---|---|---|"]
    lines += [f"| {t} | {by_type[(t, 'high')]} | {by_type[(t, 'medium')]} | {by_type[(t, 'low')]} |" for t in types]
    Path(args.out_md).write_text("\n".join(lines) + "\n")
    print(f"{len(papers)} papers, {sum(len(p['weaknesses']) for p in papers.values())} weaknesses")


if __name__ == "__main__":
    main()
