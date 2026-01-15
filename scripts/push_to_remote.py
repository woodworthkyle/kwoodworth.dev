import argparse, json, sqlite3, urllib.request
from urllib.error import HTTPError

def fetch_docs(conn):
    rows = conn.execute("""
      SELECT d.doc_key, d.title, d.slug, d.tags_json, d.html, d.content_hash, d.version, d.updated_at,
             COALESCE(ps.last_pushed_hash,'') AS last_pushed_hash
      FROM docs d
      LEFT JOIN push_state ps ON ps.doc_key = d.doc_key
      WHERE COALESCE(ps.last_pushed_hash,'') != d.content_hash
      ORDER BY d.updated_at
    """).fetchall()

    docs = []
    for r in rows:
        docs.append({
            "doc_key": r[0],
            "title": r[1] or "",
            "slug": r[2] or "",
            "tags": json.loads(r[3]) if r[3] else [],
            "html": r[4],
            "content_hash": r[5],
            "version": r[6],
            "updated_at": r[7],
        })
    return docs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS docs (
    doc_key TEXT PRIMARY KEY,
    title TEXT,
    slug TEXT,
    tags_json TEXT,
    html TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS push_state (
    doc_key TEXT PRIMARY KEY,
    last_pushed_hash TEXT NOT NULL DEFAULT '',
    last_pushed_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """)
    conn.commit()


    docs = fetch_docs(conn)

    for d in docs:
        data = json.dumps(d).encode("utf-8")
        req = urllib.request.Request(args.url, data=data, method="POST")
        req.add_header("Content-Type","application/json")
        req.add_header("Authorization", f"Token {args.token}")
        #with urllib.request.urlopen(req) as r:
        #    print(d["doc_key"], r.read().decode())
        try:
            with urllib.request.urlopen(req) as r:
                print(d["doc_key"], r.read().decode())
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(d["doc_key"], f"HTTP {e.code} {e.reason}\n{body}")
            raise

if __name__ == "__main__":
    main()
