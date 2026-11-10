"""Embedding index of the library, and ranking of library items against a round's queries.

The index is built once and updated incrementally: an item is re-embedded only when its
title/abstract text changes (tracked by hash). Ranking takes one or more query texts (e.g. one per
strand of the round protocol) and scores each item by its best cosine similarity to any query.

Usage:
    uv run --with google-genai --with numpy python embed_library.py index LIBRARY INDEX
    uv run --with google-genai --with numpy python embed_library.py rank LIBRARY INDEX QUERIES OUT

LIBRARY is JSONL with `id`, `title`, `abstract`; INDEX is a JSONL cache; QUERIES is a text file
with one query per paragraph (blank-line separated); OUT is a JSONL ranking.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from screen_abstracts import load_api_key

MODEL = "gemini-embedding-001"
BATCH = 100


def item_text(item: dict) -> str:
    return f"{item.get('title') or ''}\n\n{item.get('abstract') or ''}".strip()


def text_hash(text: str) -> str:
    return hashlib.sha256(f"{MODEL}\n{text}".encode()).hexdigest()[:16]


def embed(client: genai.Client, texts: list[str], task: str) -> list[list[float]]:
    resp = client.models.embed_content(
        model=MODEL, contents=texts, config=types.EmbedContentConfig(task_type=task))
    return [e.values for e in resp.embeddings]


def load_index(path: Path) -> dict:
    if not path.exists():
        return {}
    return {r["id"]: r for r in map(json.loads, path.open())}


def cmd_index(args, client) -> None:
    items = [json.loads(line) for line in open(args.library)]
    index = load_index(Path(args.index))
    todo = [it for it in items
            if item_text(it) and index.get(it["id"], {}).get("hash") != text_hash(item_text(it))]
    print(f"{len(items)} items, {len(todo)} to embed")
    for start in range(0, len(todo), BATCH):
        batch = todo[start:start + BATCH]
        vecs = embed(client, [item_text(it) for it in batch], "RETRIEVAL_DOCUMENT")
        for it, vec in zip(batch, vecs):
            index[it["id"]] = {"id": it["id"], "hash": text_hash(item_text(it)), "vec": vec}
        print(f"  embedded {start + len(batch)}/{len(todo)}", flush=True)
    with open(args.index, "w") as fh:
        for rec in index.values():
            fh.write(json.dumps(rec) + "\n")


def cmd_rank(args, client) -> None:
    items = {json.loads(line)["id"]: json.loads(line) for line in open(args.library)}
    index = load_index(Path(args.index))
    queries = [q.strip() for q in Path(args.queries).read_text().split("\n\n") if q.strip()]
    q = np.array(embed(client, queries, "RETRIEVAL_QUERY"))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    ids = [i for i in items if i in index]
    d = np.array([index[i]["vec"] for i in ids])
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    sims = d @ q.T  # items x queries
    best = sims.max(axis=1)
    order = np.argsort(-best)
    with open(args.out, "w") as fh:
        for rank, k in enumerate(order, 1):
            fh.write(json.dumps({"id": ids[k], "rank": rank, "score": round(float(best[k]), 4),
                                 "best_query": int(sims[k].argmax())}) + "\n")
    print(f"ranked {len(ids)} items against {len(queries)} queries "
          f"({len(items) - len(ids)} items have no text and are unranked)")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index")
    p.add_argument("library")
    p.add_argument("index")
    p = sub.add_parser("rank")
    p.add_argument("library")
    p.add_argument("index")
    p.add_argument("queries")
    p.add_argument("out")
    args = ap.parse_args()
    client = genai.Client(api_key=load_api_key())
    {"index": cmd_index, "rank": cmd_rank}[args.cmd](args, client)


if __name__ == "__main__":
    main()
