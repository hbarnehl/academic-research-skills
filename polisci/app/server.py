"""Local GUI for literature review projects.

A view over the review folders (default ~/research/lit-reviews/<slug>/) and the vault reports.
Standard library only: the server reads the files, merges them into one JSON payload per
project, and writes your overrides and notes to <slug>/user.json. The page (static/index.html)
does the rendering.

Usage:
    python polisci/app/server.py [--root ~/research/lit-reviews] [--vault ~/obsidian/phd] [--port 8765]
"""

import argparse
import json
import re
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

STATIC = Path(__file__).parent / "static"


def read_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)


def question(project: Path) -> str:
    """The review question: the first paragraph under '## Question' in R0's protocol."""
    protocol = project / "rounds" / "r0" / "protocol.md"
    if not protocol.exists():
        return ""
    m = re.search(r"## Question\s*\n+(.+?)\n\n", protocol.read_text(), flags=re.S)
    return " ".join(m.group(1).split()) if m else ""


def rounds(project: Path) -> list[dict]:
    out = []
    for d in sorted((project / "rounds").glob("*/")):
        docs = {name: (d / f"{name}.md").read_text() for name in ("protocol", "map") if (d / f"{name}.md").exists()}
        out.append({"id": d.name, "docs": docs})
    return out


def sources(project: Path, round_id: str) -> list[dict]:
    """Corpus of one round, joined with the core list and the appraisals."""
    rdir = project / "rounds" / round_id
    corpus = read_json(rdir / "corpus_annotated.json", [])
    core = {c["id"]: c for c in read_json(rdir / "core.json", [])}
    appraisals = read_json(rdir / "appraisal" / "appraisals.json", {})
    for s in corpus:
        c = core.get(s["id"])
        # Sources found by citation chasing carry an OpenAlex id; core.json adds their citekey.
        s["citekey"] = s.get("citekey") or (c and c.get("citekey"))
        a = appraisals.get(s["citekey"])
        s["core"] = c is not None
        s["core_why"] = c.get("why") if c else None
        s["in_vault"] = bool(c and c.get("in_vault")) or s.get("in_vault", False)
        s["text_status"] = "full_text" if a else ("abstract" if s.get("abstract") else "title")
        if a:
            s["appraisal"] = {k: v for k, v in a.items() if k not in ("citekey", "title", "year", "cluster")}
            md = rdir / "appraisal" / "out" / f"{s['citekey']}.md"
            s["appraisal_md"] = md.read_text() if md.exists() else None
    return corpus


def reports(slug: str, vault: Path) -> list[dict]:
    """Hub note that names this project's folder, then its chapter notes."""
    notes = vault / "notes"
    for hub in sorted(notes.glob("claude report on *.md")):
        text = hub.read_text()
        if f"lit-reviews/{slug}" not in text:
            continue
        out = [{"name": hub.stem, "text": strip_frontmatter(text)}]
        for ch in sorted(notes.glob(f"{hub.stem} - *.md")):
            out.append({"name": ch.stem, "text": strip_frontmatter(ch.read_text())})
        return out
    return []


class Handler(SimpleHTTPRequestHandler):
    root: Path
    vault: Path

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def project_dir(self, slug: str) -> Path | None:
        p = (self.root / slug).resolve()
        return p if p.parent == self.root.resolve() and (p / "rounds").is_dir() else None

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/api/projects":
            out = []
            for p in sorted(self.root.glob("*/rounds")):
                proj = p.parent
                rs = rounds(proj)
                corpus = read_json(proj / "rounds" / "r0" / "corpus_annotated.json", [])
                out.append({
                    "slug": proj.name,
                    "question": question(proj),
                    "rounds": [r["id"] for r in rs],
                    "n_sources": len(corpus),
                    "n_full_text": len(read_json(proj / "rounds" / "r0" / "appraisal" / "appraisals.json", {})),
                    "updated": datetime.fromtimestamp(max(f.stat().st_mtime for f in proj.rglob("*") if f.is_file())).strftime("%Y-%m-%d"),
                })
            return self.send_json(out)
        m = re.fullmatch(r"/api/project/([\w.-]+)", path)
        if m:
            proj = self.project_dir(m.group(1))
            if not proj:
                return self.send_json({"error": "no such project"}, 404)
            rs = rounds(proj)
            return self.send_json({
                "slug": proj.name,
                "question": question(proj),
                "rounds": rs,
                "sources": {r["id"]: sources(proj, r["id"]) for r in rs},
                "clusters": read_json(proj / "rounds" / "r0" / "clusters.json", []),
                "reports": reports(proj.name, self.vault),
                "user": read_json(proj / "user.json", {}),
                "vault": self.vault.name,
            })
        return super().do_GET()

    def do_POST(self):
        """Record an override or a note: {key, round?, decision?, reason?, note?}."""
        m = re.fullmatch(r"/api/project/([\w.-]+)/user", urlparse(self.path).path)
        proj = self.project_dir(m.group(1)) if m else None
        if not proj:
            return self.send_json({"error": "no such project"}, 404)
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        user = read_json(proj / "user.json", {})
        entry = user.setdefault(data["key"], {})
        if "note" in data:
            entry["note"] = data["note"]
        if "decision" in data:
            overrides = entry.setdefault("overrides", {})
            if data["decision"]:
                overrides[data["round"]] = {
                    "decision": data["decision"],
                    "reason": data.get("reason", ""),
                    "by": "user",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            else:
                overrides.pop(data["round"], None)
        (proj / "user.json").write_text(json.dumps(user, indent=2, ensure_ascii=False) + "\n")
        self.send_json(user)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="~/research/lit-reviews")
    ap.add_argument("--vault", default="~/obsidian/phd")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    Handler.root = Path(args.root).expanduser()
    Handler.vault = Path(args.vault).expanduser()
    print(f"Serving on http://localhost:{args.port}")
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
