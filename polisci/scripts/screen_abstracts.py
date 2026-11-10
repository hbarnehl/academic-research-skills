"""Abstract screening with Gemini Flash.

Reads candidates (JSONL with at least `id`, `title`, `abstract`), screens them in batches against
a round protocol (markdown), and writes one decision per candidate to an output JSONL.
Already-screened ids in the output file are skipped, so the script can be re-run after a failure.

Usage:
    uv run --with google-genai python screen_abstracts.py CANDIDATES PROTOCOL OUT [--batch 40]
"""

import argparse
import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"
SECRETS_FILE = Path.home() / ".config/secrets/env"

PROMPT = """You screen candidate sources for a literature review. The review protocol is below.

<protocol>
{protocol}
</protocol>

For each candidate, decide from title and abstract only:
- "include": clearly in scope (name the strand)
- "maybe": possibly in scope, needs full text, or no abstract but the title suggests relevance
- "defer": out of scope for this round but matches a deferred topic in the protocol (give the
  topic name as "defer_to"); only if the protocol lists deferred topics
- "exclude": out of scope
Give a reason of at most 20 words. Do not guess content that is not in the title or abstract.

Return a JSON list with one object per candidate, in the same order:
{{"id": ..., "decision": "include"|"maybe"|"defer"|"exclude", "strand": "A"|"B"|null,
  "defer_to": null or topic name, "reason": ...}}

<candidates>
{candidates}
</candidates>
"""


def load_api_key() -> str:
    """GOOGLE_API_KEY from the environment or the secrets file (never printed)."""
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    for line in SECRETS_FILE.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?GOOGLE_API_KEY=(.*)", line)
        if m:
            return m.group(1).strip().strip("\"'")
    raise SystemExit("GOOGLE_API_KEY not found")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("protocol")
    ap.add_argument("out")
    ap.add_argument("--batch", type=int, default=40)
    args = ap.parse_args()

    protocol = Path(args.protocol).read_text()
    cands = [json.loads(line) for line in open(args.candidates)]
    out = Path(args.out)
    done = {json.loads(line)["id"] for line in out.open()} if out.exists() else set()
    todo = [c for c in cands if c["id"] not in done]
    print(f"{len(cands)} candidates, {len(done)} already screened, {len(todo)} to go")

    client = genai.Client(api_key=load_api_key())
    for start in range(0, len(todo), args.batch):
        batch = todo[start:start + args.batch]
        # Abstracts are truncated to keep batches small; the opening usually carries the scope.
        lines = [json.dumps({"id": c["id"], "title": c.get("title"),
                             "abstract": (c.get("abstract") or "")[:1500] or None})
                 for c in batch]
        resp = client.models.generate_content(
            model=MODEL,
            contents=PROMPT.format(protocol=protocol, candidates="\n".join(lines)),
            config=types.GenerateContentConfig(response_mime_type="application/json",
                                               temperature=0),
        )
        decisions = {d["id"]: d for d in json.loads(resp.text)}
        with out.open("a") as fh:
            for c in batch:
                d = decisions.get(c["id"])
                if d is None:
                    print(f"  missing decision for {c['id']}, will retry on next run")
                    continue
                fh.write(json.dumps({**d, "id": c["id"]}) + "\n")
        print(f"  screened {start + len(batch)}/{len(todo)}")


if __name__ == "__main__":
    main()
