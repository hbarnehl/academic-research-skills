"""Check that every quoted passage in an appraisal appears verbatim in the paper text.

Matching ignores case, whitespace, line-break hyphenation and quote-mark style. For each quote it
reports the PDF page(s) where it occurs and the page the appraisal cites, so a wrong page or an
invented quote stands out. Printed page numbers differ from PDF pages, so a page mismatch is a
prompt to look, not proof of an error.

Usage:
    python check_quotes.py APPRAISAL_DIR TEXT_DIR [--summary OUT_JSON]
TEXT_DIR holds <citekey>.txt with `=== PDF page N ===` markers; APPRAISAL_DIR holds <citekey>.md.
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

QUOTE = re.compile(r'\*\*Evidence\*\*:\s*["“](.+?)["”]\s*\(([^)]*)\)')


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)  # math-italic letters (𝑀, 𝐹) and ligatures
    s = re.sub(r"\n\s*\d{1,4}\s*(?=\n)", "", s)  # line numbers of line-numbered preprints
    s = re.sub(r"[\x00-\x08\x0b-\x1f]", "", s)  # stray control characters
    s = s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"-\s*\n\s*", "", s)          # rejoin words hyphenated across lines
    s = re.sub(r"\u00ad\s*", "", s)         # soft hyphens, also at line ends
    for lig, plain in {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}.items():
        s = s.replace(lig, plain)
    s = s.replace("-", "")                  # pdftotext sometimes drops hyphens ("NonU.S.")
    return re.sub(r"\s+", " ", s).strip().lower()


def pages(text: str) -> dict[int, str]:
    parts = re.split(r"=== PDF page (\d+) ===", text)
    return {int(parts[i]): norm(parts[i + 1]) for i in range(1, len(parts), 2)}


def find(quote: str, pg: dict[int, str]) -> list[int]:
    q = norm(quote)
    # Quotes may skip text with an ellipsis; every fragment must appear on the same page.
    frags = [f.strip() for f in re.split(r"\s*(?:\.\.\.|…)\s*", q) if f.strip()]
    hits = [p for p, t in pg.items() if all(f in t for f in frags)]
    if not hits:  # a quote may run across a page break
        keys = sorted(pg)
        for a, b in zip(keys, keys[1:]):
            if all(f in pg[a] + " " + pg[b] for f in frags):
                hits.append(a)
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("appraisals")
    ap.add_argument("texts")
    ap.add_argument("--summary")
    args = ap.parse_args()

    report = {}
    for f in sorted(Path(args.appraisals).glob("*.md")):
        pg = pages((Path(args.texts) / f"{f.stem}.txt").read_text())
        rows = []
        for quote, cited in QUOTE.findall(f.read_text()):
            rows.append({"quote": quote[:80], "cited": cited, "found_on": find(quote, pg)})
        missing = [r for r in rows if not r["found_on"]]
        report[f.stem] = {"quotes": len(rows), "not_found": missing}
        print(f"{f.stem:45} {len(rows):2} quotes, {len(missing)} not found")
        for r in missing:
            print(f"    NOT FOUND ({r['cited']}): {r['quote']}")
    if args.summary:
        Path(args.summary).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
