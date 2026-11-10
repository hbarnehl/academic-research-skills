"""Cluster a round's corpus by embedding and have Gemini name each cluster (the literature map).

Clusters with k-means on the cached embeddings (`embed_library.py`), then sends each cluster's
most central titles and abstract openings to Gemini Flash for a short name and description.
Descriptions rest on abstracts only, which the output says.

Usage:
    uv run --with google-genai --with numpy --with scikit-learn python cluster_map.py \
        CORPUS OUT_JSON --index INDEX [INDEX ...] [--k 10] [--scan]

--scan prints silhouette scores for k = 5..15 and exits, to help choose k.
"""

import argparse
import json

import numpy as np
from google import genai
from google.genai import types
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from screen_abstracts import MODEL, load_api_key

PROMPT = """Below are the most central papers (title and abstract opening) of one cluster in a
literature review on remote sensing of armed conflict and on conflict event data and its biases.

Return JSON: {{"name": short cluster name (max 8 words),
"description": 2-3 sentences on what these papers study and how, based only on what is below}}

{papers}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("out")
    ap.add_argument("--index", nargs="+", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--scan", action="store_true")
    args = ap.parse_args()

    corpus = [json.loads(line) for line in open(args.corpus)]
    vecs = {}
    for f in args.index:
        for line in open(f):
            r = json.loads(line)
            vecs[r["id"]] = r["vec"]
    corpus = [c for c in corpus if c["id"] in vecs]
    X = np.array([vecs[c["id"]] for c in corpus])
    X /= np.linalg.norm(X, axis=1, keepdims=True)

    if args.scan:
        for k in range(5, 16):
            labels = KMeans(k, n_init=10, random_state=0).fit_predict(X)
            print(k, round(silhouette_score(X, labels, metric="cosine"), 4))
        return

    km = KMeans(args.k, n_init=10, random_state=0).fit(X)
    dist = np.linalg.norm(X - km.cluster_centers_[km.labels_], axis=1)
    client = genai.Client(api_key=load_api_key())
    clusters = []
    for k in range(args.k):
        idx = sorted(np.where(km.labels_ == k)[0], key=lambda i: dist[i])
        members = [corpus[i] for i in idx]
        papers = "\n".join(f"- {m['title']} ({m['year']}): {(m.get('abstract') or '')[:300]}"
                           for m in members[:15])
        resp = client.models.generate_content(
            model=MODEL, contents=PROMPT.format(papers=papers),
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
        label = json.loads(resp.text)
        clusters.append({"cluster": k, "name": label["name"], "description": label["description"],
                         "basis": "abstracts of the 15 most central papers",
                         "size": len(members), "members": [m["id"] for m in members]})
        print(f"{k:>2} {len(members):>4}  {label['name']}", flush=True)
    clusters.sort(key=lambda c: -c["size"])
    with open(args.out, "w") as fh:
        json.dump(clusters, fh, indent=1)


if __name__ == "__main__":
    main()
