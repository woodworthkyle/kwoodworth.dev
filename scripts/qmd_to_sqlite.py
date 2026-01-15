#!/usr/bin/env python3
"""
qmd_to_sqlite.py

Render a Quarto .qmd file to HTML, extract body contents as an HTML fragment,
parse YAML front matter for title/slug/tags (and optional doc_key),
compute a content hash, and insert/update into SQLite using SLUG as the lookup key.

Schema (created if missing):

    doc_key TEXT PRIMARY KEY,
    title TEXT,
    slug TEXT,
    tags_json TEXT,
    html TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))

Behavior:
- Row identity for updates is slug (requires slug UNIQUE; we create a unique index).
- If slug exists: update that row (preserve existing doc_key).
- If slug not found: insert new row with doc_key.
- If content_hash changes: version += 1; otherwise version unchanged.

Usage:
  python qmd_to_sqlite.py path/to/post.qmd --db content.db

Optional:
  --doc-key <key>          suggested doc_key for new inserts (ignored on slug-updates)
  --table <name>           default: docs
  --keep-html              keep rendered HTML in a temp sibling folder
  --no-execute                disable code execution during render (default: execute)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# Optional dependencies:
#   pip install beautifulsoup4 pyyaml
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None


FRONT_MATTER_RE = re.compile(r"(?s)\A---\s*\n(.*?)\n---\s*\n")


@dataclass
class FrontMatter:
    title: Optional[str]
    slug: Optional[str]
    tags: List[str]
    doc_key: Optional[str]


def ensure_deps():
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is required. Install with: pip install beautifulsoup4")


def run_quarto_render(qmd_path: Path, out_dir: Path, execute: bool) -> Path:
    if shutil.which("quarto") is None:
        raise RuntimeError("quarto not found on PATH. Install Quarto or add it to PATH.")

    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "quarto",
        "render",
        str(qmd_path),
        "--to",
        "html",
        "--output-dir",
        str(out_dir),
    ]
    if not execute:
        cmd.append("--no-execute")

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Quarto render failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}\n"
        )

    html_path = out_dir / (qmd_path.stem + ".html")
    if not html_path.exists():
        candidates = sorted(out_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise RuntimeError(f"Render succeeded but no HTML found in {out_dir}")
        html_path = candidates[0]

    return html_path


def parse_front_matter(qmd_text: str) -> FrontMatter:
    m = FRONT_MATTER_RE.search(qmd_text)
    if not m:
        return FrontMatter(title=None, slug=None, tags=[], doc_key=None)

    data = yaml.safe_load(m.group(1)) or {}
    if not isinstance(data, dict):
        data = {}

    title = data.get("title")
    slug = data.get("slug")
    doc_key = data.get("doc_key") or data.get("docKey") or data.get("key")

    tags_raw = data.get("tags", data.get("categories", []))
    tags: List[str] = []
    if isinstance(tags_raw, list):
        tags = [str(x).strip() for x in tags_raw if str(x).strip()]
    elif isinstance(tags_raw, str):
        tags = [p.strip() for p in tags_raw.split(",") if p.strip()]
    elif tags_raw is None:
        tags = []
    else:
        s = str(tags_raw).strip()
        tags = [s] if s else []

    tags = sorted(set(tags))

    title = str(title) if title is not None else None
    slug = str(slug) if slug is not None else None
    doc_key = str(doc_key) if doc_key is not None else None

    return FrontMatter(title=title, slug=slug, tags=tags, doc_key=doc_key)


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s or "untitled"


def extract_body_fragment(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    body = soup.body
    if body is None:
        return html_text.strip()

    for tag in body.find_all(["script", "style", "noscript"]):
        tag.decompose()

    main = body.find("main")
    container = main if main is not None else body

    fragment = "".join(str(x) for x in container.contents).strip()
    return fragment


def sha256_hex(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def stable_doc_key_from_path(qmd_path: Path) -> str:
    try:
        rel = qmd_path.relative_to(Path.cwd())
        key_src = str(rel).replace(os.sep, "/")
    except Exception:
        key_src = str(qmd_path).replace(os.sep, "/")
    return sha256_hex(key_src)


def init_db(conn: sqlite3.Connection, table: str) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
        doc_key TEXT PRIMARY KEY,
        title TEXT,
        slug TEXT,
        tags_json TEXT,
        html TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # IMPORTANT for "update-by-slug": enforce one row per slug.
    conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_slug_unique ON {table}(slug);")
    conn.commit()


def choose_unique_doc_key(conn: sqlite3.Connection, table: str, preferred: str, slug: str) -> str:
    """
    Ensure doc_key doesn't collide with an existing row.
    If preferred is already taken, generate a deterministic alternative.
    """
    exists = conn.execute(
        f"SELECT 1 FROM {table} WHERE doc_key = ? LIMIT 1",
        (preferred,),
    ).fetchone()
    if not exists:
        return preferred

    # Deterministic fallback that depends on slug (and preferred),
    # so repeated inserts are stable.
    alt = sha256_hex(f"{slug}::{preferred}")
    exists2 = conn.execute(
        f"SELECT 1 FROM {table} WHERE doc_key = ? LIMIT 1",
        (alt,),
    ).fetchone()
    if not exists2:
        return alt

    # Very unlikely; last-resort: add a numeric suffix until free.
    i = 2
    while True:
        alt2 = sha256_hex(f"{slug}::{preferred}::{i}")
        exists3 = conn.execute(
            f"SELECT 1 FROM {table} WHERE doc_key = ? LIMIT 1",
            (alt2,),
        ).fetchone()
        if not exists3:
            return alt2
        i += 1


def upsert_document_by_slug(
    conn: sqlite3.Connection,
    table: str,
    slug: str,
    doc_key_for_insert: str,
    title: Optional[str],
    tags: List[str],
    html: str,
    content_hash: str,
) -> Tuple[str, int, bool, bool]:
    """
    Insert or update using slug as the lookup key.

    Returns:
      (doc_key_used, version, changed_content, was_insert)
    """
    tags_json = json.dumps(tags, ensure_ascii=False)

    row = conn.execute(
        f"SELECT doc_key, content_hash, version FROM {table} WHERE slug = ?",
        (slug,),
    ).fetchone()

    if row is None:
        # Insert new row
        doc_key_unique = choose_unique_doc_key(conn, table, doc_key_for_insert, slug)
        conn.execute(
            f"""
            INSERT INTO {table}
              (doc_key, title, slug, tags_json, html, content_hash, version, updated_at)
            VALUES
              (?, ?, ?, ?, ?, ?, 0, datetime('now'))
            """,
            (doc_key_unique, title, slug, tags_json, html, content_hash),
        )
        conn.commit()
        return doc_key_unique, 0, True, True

    existing_doc_key, old_hash, old_version = row[0], row[1], int(row[2])

    if old_hash != content_hash:
        new_version = old_version + 1
        conn.execute(
            f"""
            UPDATE {table}
            SET title = ?,
                tags_json = ?,
                html = ?,
                content_hash = ?,
                version = ?,
                updated_at = datetime('now')
            WHERE slug = ?
            """,
            (title, tags_json, html, content_hash, new_version, slug),
        )
        conn.commit()
        return existing_doc_key, new_version, True, False

    # Content unchanged: update metadata only
    conn.execute(
        f"""
        UPDATE {table}
        SET title = ?,
            tags_json = ?,
            updated_at = datetime('now')
        WHERE slug = ?
        """,
        (title, tags_json, slug),
    )
    conn.commit()
    return existing_doc_key, old_version, False, False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> None:
    ensure_deps()

    ap = argparse.ArgumentParser()
    ap.add_argument("qmd", type=str, help="Path to input .qmd file")
    ap.add_argument("--db", type=str, required=True, help="Path to sqlite database file")
    ap.add_argument("--table", type=str, default="docs", help="Table name (default: documents)")
    ap.add_argument("--doc-key", type=str, default="", help="Preferred doc_key for NEW inserts only")
    ap.add_argument("--keep-html", action="store_true", help="Keep rendered HTML in .quarto_render_tmp")
    ap.add_argument("--no-execute", action="store_false", help="Disable code execution during render")
    args = ap.parse_args()

    qmd_path = Path(args.qmd).expanduser().resolve()
    if not qmd_path.exists():
        print(f"Input file not found: {qmd_path}", file=sys.stderr)
        sys.exit(1)

    qmd_text = read_text(qmd_path)
    fm = parse_front_matter(qmd_text)

    # slug is REQUIRED for update-by-slug; we derive it if missing
    slug = fm.slug
    if not slug:
        slug = slugify(fm.title) if fm.title else slugify(qmd_path.stem)

    # doc_key is used ONLY for new inserts; if updating by slug, existing doc_key is preserved
    preferred_doc_key = (args.doc_key.strip()
                         or (fm.doc_key.strip() if fm.doc_key else "")
                         or stable_doc_key_from_path(qmd_path))

    # Render
    if args.keep_html:
        out_dir = qmd_path.parent / ".quarto_render_tmp"
        out_dir.mkdir(exist_ok=True)
        html_path = run_quarto_render(qmd_path, out_dir, execute=args.no_execute)
        html_text = read_text(html_path)
    else:
        with tempfile.TemporaryDirectory(prefix="quarto_render_") as td:
            html_path = run_quarto_render(qmd_path, Path(td), execute=args.no_execute)
            html_text = read_text(html_path)

    fragment = extract_body_fragment(html_text)
    content_hash = sha256_hex(fragment)

    # DB write
    db_path = Path(args.db).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        init_db(conn, args.table)
        doc_key_used, version, changed, inserted = upsert_document_by_slug(
            conn=conn,
            table=args.table,
            slug=slug,
            doc_key_for_insert=preferred_doc_key,
            title=fm.title,
            tags=fm.tags,
            html=fragment,
            content_hash=content_hash,
        )
    finally:
        conn.close()

    result = {
        "doc_key": doc_key_used,
        "title": fm.title,
        "slug": slug,
        "tags": fm.tags,
        "content_hash": content_hash,
        "version": version,
        "changed_content": changed,
        "inserted": inserted,
        "db": str(db_path),
        "table": args.table,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
