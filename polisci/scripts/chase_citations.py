"""Backward and forward citation chasing via OpenAlex.

Steps:
  resolve  Match seed papers (JSONL with `id`, `doi`, `title`, `year`) to OpenAlex works, by DOI
           first, then by title search within +-1 year (accepted only on a close title match).
  chase    For every resolved seed, collect the works it cites (backward, `referenced_works`) and
           the works citing it (forward, `filter=cites:`), fetch their metadata, and write one
           candidate per work with the seeds it is linked to. Works already in the library (by
           OpenAlex id or DOI) are dropped.

Usage:
    uv run python chase_citations.py resolve SEEDS RESOLVED
    uv run python chase_citations.py chase RESOLVED LIBRARY OUT [--max-forward 500]
"""

import argparse
import difflib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.openalex.org"
SECRETS_FILE = Path.home() / ".config/secrets/env"
FIELDS = "id,doi,title,publication_year,authorships,primary_location,cited_by_count,abstract_inverted_index,type"


def load_api_key() -> str | None:
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        return key
    for line in SECRETS_FILE.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?OPENALEX_API_KEY=(.*)", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


API_KEY = load_api_key()


def get(path: str, **params) -> dict:
    if API_KEY:
        params["api_key"] = API_KEY
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            if e.code != 429 and e.code < 500:
                raise RuntimeError(f"OpenAlex HTTP {e.code} for {path}") from None
        except urllib.error.URLError:
            pass
        time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenAlex request failed repeatedly: {path}")


def short_id(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    return re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi.strip().lower())


def norm_title(t: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()


def abstract(inv: dict | None) -> str | None:
    """Rebuild the abstract from OpenAlex's inverted index."""
    if not inv:
        return None
    pos = [(i, w) for w, idx in inv.items() for i in idx]
    return " ".join(w for _, w in sorted(pos))


def to_record(w: dict) -> dict:
    loc = w.get("primary_location") or {}
    return {
        "openalex": short_id(w["id"]),
        "doi": norm_doi(w.get("doi")),
        "title": w.get("title"),
        "year": w.get("publication_year"),
        "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:5],
        "venue": ((loc.get("source") or {}).get("display_name")),
        "type": w.get("type"),
        "cited_by_count": w.get("cited_by_count"),
        "abstract": abstract(w.get("abstract_inverted_index")),
    }


def resolve_one(seed: dict) -> dict | None:
    doi = norm_doi(seed.get("doi"))
    if doi:
        w = get(f"/works/doi:{doi}", select=FIELDS + ",referenced_works")
        if w:
            return w
    if not seed.get("title"):
        return None
    params = {"search": seed["title"], "per-page": 5, "select": FIELDS + ",referenced_works"}
    if str(seed.get("year", "")).isdigit():
        y = int(seed["year"])
        params["filter"] = f"publication_year:{y - 1}-{y + 1}"
    for w in get("/works", **params).get("results", []):
        ratio = difflib.SequenceMatcher(None, norm_title(seed["title"]), norm_title(w.get("title"))).ratio()
        if ratio >= 0.9:
            return w
    return None


def cmd_resolve(args) -> None:
    seeds = [json.loads(line) for line in open(args.seeds)]
    n_ok = 0
    with open(args.resolved, "w") as fh:
        for s in seeds:
            w = resolve_one(s)
            rec = {"id": s["id"], "resolved": w is not None}
            if w:
                n_ok += 1
                rec.update(to_record(w))
                rec["referenced_works"] = [short_id(r) for r in w.get("referenced_works", [])]
            fh.write(json.dumps(rec) + "\n")
    print(f"resolved {n_ok}/{len(seeds)} seeds")


def fetch_works(ids: list[str]) -> list[dict]:
    """Batch-fetch metadata for OpenAlex ids (50 per request)."""
    out = []
    for start in range(0, len(ids), 50):
        chunk = ids[start:start + 50]
        res = get("/works", filter="openalex_id:" + "|".join(chunk), select=FIELDS, **{"per-page": 50})
        out.extend(res.get("results", []))
    return out


def citing_works(work_id: str, cap: int) -> tuple[list[dict], int]:
    """Works citing `work_id`, most-cited first, up to `cap`. Returns (works, total count)."""
    works, cursor, total = [], "*", 0
    while cursor and len(works) < cap:
        res = get("/works", filter=f"cites:{work_id}", select=FIELDS, sort="cited_by_count:desc",
                  cursor=cursor, **{"per-page": 200})
        total = res.get("meta", {}).get("count", 0)
        works.extend(res.get("results", []))
        cursor = res.get("meta", {}).get("next_cursor")
        if not res.get("results"):
            break
    return works[:cap], total


def cmd_chase(args) -> None:
    seeds = [json.loads(line) for line in open(args.resolved)]
    seeds = [s for s in seeds if s["resolved"]]
    library = [json.loads(line) for line in open(args.library)]
    lib_dois = {norm_doi(x.get("doi")) for x in library} - {None}
    seed_ids = {s["openalex"] for s in seeds}

    links: dict[str, dict] = {}  # openalex id -> {"backward": [seed ids], "forward": [seed ids]}
    meta: dict[str, dict] = {}
    truncated = []
    for s in seeds:
        for ref in s["referenced_works"]:
            links.setdefault(ref, {"backward": [], "forward": []})["backward"].append(s["id"])
        works, total = citing_works(s["openalex"], args.max_forward)
        if total > len(works):
            truncated.append((s["id"], total))
        for w in works:
            wid = short_id(w["id"])
            meta[wid] = to_record(w)
            links.setdefault(wid, {"backward": [], "forward": []})["forward"].append(s["id"])
        print(f"  {s['id']}: {len(s['referenced_works'])} refs, {len(works)}/{total} citing", flush=True)

    missing = [wid for wid in links if wid not in meta]
    print(f"fetching metadata for {len(missing)} referenced works")
    for w in fetch_works(missing):
        meta[short_id(w["id"])] = to_record(w)

    n_in_lib = 0
    rows = []
    for wid, ln in links.items():
        rec = meta.get(wid)
        if rec is None or wid in seed_ids:
            continue
        if rec["doi"] in lib_dois:
            n_in_lib += 1
            continue
        linked = sorted(set(ln["backward"]) | set(ln["forward"]))
        rows.append({"id": wid, **rec, "pool": "citation",
                     "cited_by_seeds": sorted(set(ln["backward"])),
                     "cites_seeds": sorted(set(ln["forward"])),
                     "n_seeds": len(linked)})
    rows.sort(key=lambda r: (-r["n_seeds"], -(r["cited_by_count"] or 0)))
    with open(args.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(rows)} candidates written ({n_in_lib} already in library dropped)")
    for sid, total in truncated:
        print(f"  forward truncated for {sid}: kept {args.max_forward} of {total} (most cited)")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resolve")
    p.add_argument("seeds")
    p.add_argument("resolved")
    p = sub.add_parser("chase")
    p.add_argument("resolved")
    p.add_argument("library")
    p.add_argument("out")
    p.add_argument("--max-forward", type=int, default=500)
    args = ap.parse_args()
    {"resolve": cmd_resolve, "chase": cmd_chase}[args.cmd](args)


if __name__ == "__main__":
    main()
