"""Keyword search in OpenAlex for the gaps that library and citation chasing left (pool 4).

Runs each query (one per line in QUERIES, `#` lines are comments) as an OpenAlex title/abstract
search, keeps the top N per query by relevance, and drops works already seen in this round
(any id or DOI in the SEEN files). Each candidate records which queries found it.

Usage:
    uv run python keyword_search.py QUERIES OUT --seen FILE [FILE ...] [--per-query 50]
"""

import argparse
import json

from chase_citations import FIELDS, get, norm_doi, short_id, to_record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("queries")
    ap.add_argument("out")
    ap.add_argument("--seen", nargs="+", default=[])
    ap.add_argument("--per-query", type=int, default=50)
    args = ap.parse_args()

    seen_ids, seen_dois = set(), set()
    for f in args.seen:
        for line in open(f):
            r = json.loads(line)
            seen_ids.add(r.get("id"))
            seen_ids.add(r.get("openalex"))
            seen_dois.add(norm_doi(r.get("doi")))
    seen_dois.discard(None)

    queries = [q.strip() for q in open(args.queries) if q.strip() and not q.startswith("#")]
    found: dict[str, dict] = {}
    for q in queries:
        res = get("/works", filter=f"title_and_abstract.search:{q}", select=FIELDS,
                  sort="relevance_score:desc", **{"per-page": args.per_query})
        n_new = 0
        for w in res.get("results", []):
            wid = short_id(w["id"])
            rec = to_record(w)
            if wid in seen_ids or rec["doi"] in seen_dois:
                continue
            if wid not in found:
                n_new += 1
                found[wid] = {"id": wid, **rec, "pool": "search", "queries": []}
            found[wid]["queries"].append(q)
        print(f"  {res.get('meta', {}).get('count', 0):>7} hits, {n_new:>3} new: {q}", flush=True)

    with open(args.out, "w") as fh:
        for r in found.values():
            fh.write(json.dumps(r) + "\n")
    print(f"{len(found)} new candidates from {len(queries)} queries")


if __name__ == "__main__":
    main()
