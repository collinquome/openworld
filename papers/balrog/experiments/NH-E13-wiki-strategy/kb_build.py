#!/usr/bin/env python3
"""
kb_build.py — NH-E13 wiki knowledge-base builder (nethackwiki.com -> local FTS5 KB)

Idempotent / add-only: re-running only fetches pages that are not already
present as rows in `pages` (keyed by resolved page_title). Existing rows are
never overwritten or deleted, per the operator spec in KB.md.

Usage:
    python3 kb_build.py            # build/update wiki_kb.sqlite + manifest
    python3 kb_build.py --sanity   # run the 3 FTS5 sanity queries only
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_URL = "https://nethackwiki.com/w/api.php"
USER_AGENT = "botxiv-research-kb/0.1 (contact: aleph@botxiv.org)"
ADDED_BY = "A001-phaseL-session1 (Fable 5)"
SLEEP_S = 1.0

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki_kb.sqlite")
MANIFEST_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "wiki_kb_manifest.json"
)

# (requested_title, reason)
BATCH = [
    ("Standard strategy", "core strategy arm (NH-E13)"),
    ("Force bolt", "Wizard combat doctrine (NH-E14)"),
    ("Wizard", "role strategy page (NH-E14)"),
    ("Healer", "role strategy page (NH-E14)"),
    ("Wand", "zap doctrine + wand identification (NH-E14/E18)"),
    ("Potion", "quaff doctrine + potion prices (NH-E14/E18)"),
    ("Scroll", "read doctrine + scroll prices (NH-E14/E18)"),
    ("Price identification", "THE price-ID reference (NH-E18 dot-connector)"),
    ("Weapon", "wield doctrine (P2)"),
    ("Armor", "armor doctrine (P3)"),
    ("Spellbook", "spell mechanics incl. failure rates (NH-E14)"),
    ("Elbereth", "carded already, keep the reference (E-NH5)"),
    ("Ring", "ring prices/effects (NH-E18)"),
    ("Comestible", "food economy reference"),
    ("Shopkeeper", "shop mechanics/price mechanics (NH-E18)"),
]


def api_get(params):
    q = dict(params)
    q["format"] = "json"
    url = API_URL + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_page(title):
    """Fetch latest revision wikitext for `title`, following redirects.

    Returns dict: resolved_title, url, revision_id, revision_date, wikitext
    or raises RuntimeError on hard failure (missing page / API unreachable).
    """
    data = api_get(
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content|ids|timestamp",
            "rvslots": "main",
            "redirects": "1",
            "titles": title,
        }
    )
    query = data.get("query", {})
    pages = query.get("pages", {})
    if not pages:
        raise RuntimeError(f"'{title}': no 'pages' in API response: {data}")

    page = next(iter(pages.values()))
    if "missing" in page:
        raise RuntimeError(f"'{title}': page missing (404) on nethackwiki")

    resolved_title = page.get("title", title)
    revisions = page.get("revisions")
    if not revisions:
        raise RuntimeError(f"'{title}': no revisions returned: {page}")

    rev = revisions[0]
    revid = rev["revid"]
    timestamp = rev["timestamp"]
    wikitext = rev["slots"]["main"]["*"]

    redirect_note = None
    redirects = query.get("redirects")
    if redirects:
        # e.g. [{"from": "Wand", "to": "Wand"}] usually no-op, but track it
        redirect_note = redirects

    url = "https://nethackwiki.com/wiki/" + urllib.parse.quote(
        resolved_title.replace(" ", "_")
    )

    return {
        "requested_title": title,
        "resolved_title": resolved_title,
        "url": url,
        "revision_id": revid,
        "revision_date": timestamp,
        "wikitext": wikitext,
        "redirect_note": redirect_note,
    }


def wikitext_to_plaintext(wikitext):
    """Crude wikitext -> plaintext cleanup.

    Keeps table cell text (price tables matter) but strips markup noise:
    templates, refs, file/image links, wiki-link brackets (keeps display
    text / target), bold/italic markup, HTML comments and tags.
    """
    text = wikitext

    # Drop HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Drop <ref>...</ref> blocks and self-closing <ref .../>
    text = re.sub(r"<ref[^>/]*/>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Strip templates {{...}} - handle simple nesting by repeated passes
    for _ in range(6):
        new_text = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if new_text == text:
            break
        text = new_text

    # File/Image links: [[File:...]] / [[Image:...]] -> drop entirely
    text = re.sub(
        r"\[\[(?:File|Image):[^\]]*\]\]", "", text, flags=re.IGNORECASE
    )

    # Wiki links [[target|display]] -> display ; [[target]] -> target
    def _link_repl(m):
        inner = m.group(1)
        parts = inner.split("|")
        return parts[-1]

    text = re.sub(r"\[\[([^\]]*)\]\]", _link_repl, text)

    # External links [http://... display] -> display ; [http://...] -> drop
    def _ext_repl(m):
        inner = m.group(1)
        parts = inner.split(None, 1)
        if len(parts) == 2:
            return parts[1]
        return ""

    text = re.sub(r"\[([^\]]*)\]", _ext_repl, text)

    # Table markup: keep cell text. Convert row/cell separators to spacing.
    # Remove table/row/cell wiki-markup tokens at line starts.
    text = re.sub(r"^\{\|.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\|\}.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\|-.*$", "", text, flags=re.MULTILINE)
    # Header cells "! a !! b" / "!" at line start
    text = re.sub(r"^!\s*", "", text, flags=re.MULTILINE)
    text = text.replace("!!", " | ")
    # Cell/row leading markers "| " or "|+ " at line start -> keep content
    text = re.sub(r"^\|\+?\s*", "", text, flags=re.MULTILINE)
    # Inline cell separator "||" -> pipe-space
    text = text.replace("||", " | ")

    # Bold/italic markup
    text = text.replace("'''''", "").replace("'''", "").replace("''", "")

    # Section headers === X === -> X
    text = re.sub(r"^=+\s*(.*?)\s*=+\s*$", r"\1", text, flags=re.MULTILINE)

    # Remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Collapse excess whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = text.strip()

    return text


def ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            page_title TEXT PRIMARY KEY,
            url TEXT,
            revision_id INTEGER,
            revision_date TEXT,
            wikitext TEXT,
            plaintext TEXT,
            sha256 TEXT,
            added_by TEXT,
            added_when TEXT,
            reason TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            page_title,
            plaintext,
            content='pages',
            content_rowid='rowid'
        )
        """
    )
    # Triggers to keep FTS in sync (harmless for add-only usage, but correct)
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
            INSERT INTO pages_fts(rowid, page_title, plaintext)
            VALUES (new.rowid, new.page_title, new.plaintext);
        END
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
            INSERT INTO pages_fts(pages_fts, rowid, page_title, plaintext)
            VALUES ('delete', old.rowid, old.page_title, old.plaintext);
        END
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
            INSERT INTO pages_fts(pages_fts, rowid, page_title, plaintext)
            VALUES ('delete', old.rowid, old.page_title, old.plaintext);
            INSERT INTO pages_fts(rowid, page_title, plaintext)
            VALUES (new.rowid, new.page_title, new.plaintext);
        END
        """
    )
    conn.commit()


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    return []


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def build():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    manifest = load_manifest()
    manifest_titles = {m["page"] for m in manifest}

    existing = {
        row[0] for row in conn.execute("SELECT page_title FROM pages").fetchall()
    }

    results = []
    failures = []

    for requested_title, reason in BATCH:
        # Skip if we already have this requested title resolved & stored.
        # We check both the manifest (by requested-title match on 'page')
        # and DB existing rows in case resolution differs.
        already = False
        for m in manifest:
            if m.get("requested_title", m.get("page")) == requested_title and m[
                "page"
            ] in existing:
                already = True
                break
        if already:
            print(f"[skip] '{requested_title}' already in KB")
            continue

        print(f"[fetch] '{requested_title}' ...")
        try:
            fetched = fetch_page(requested_title)
        except Exception as e:
            print(f"[FAIL] '{requested_title}': {e}")
            failures.append({"requested_title": requested_title, "error": str(e)})
            time.sleep(SLEEP_S)
            continue

        resolved_title = fetched["resolved_title"]

        if resolved_title in existing:
            print(
                f"[skip] '{requested_title}' resolves to '{resolved_title}' "
                f"already in KB"
            )
            time.sleep(SLEEP_S)
            continue

        wikitext = fetched["wikitext"]
        plaintext = wikitext_to_plaintext(wikitext)
        sha256 = hashlib.sha256(wikitext.encode("utf-8")).hexdigest()
        added_when = datetime.now(timezone.utc).isoformat()

        full_reason = reason
        if resolved_title != requested_title:
            full_reason = (
                f"{reason} [requested title: '{requested_title}', "
                f"redirected to '{resolved_title}']"
            )

        conn.execute(
            """
            INSERT INTO pages
                (page_title, url, revision_id, revision_date, wikitext,
                 plaintext, sha256, added_by, added_when, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_title,
                fetched["url"],
                fetched["revision_id"],
                fetched["revision_date"],
                wikitext,
                plaintext,
                sha256,
                ADDED_BY,
                added_when,
                full_reason,
            ),
        )
        conn.commit()
        existing.add(resolved_title)

        manifest_entry = {
            "page": resolved_title,
            "requested_title": requested_title,
            "url": fetched["url"],
            "revision_id": fetched["revision_id"],
            "revision_date": fetched["revision_date"],
            "sha256": sha256,
            "added_by": ADDED_BY,
            "added_when": added_when,
            "reason": full_reason,
        }
        manifest.append(manifest_entry)
        save_manifest(manifest)  # save incrementally so partial runs persist

        results.append(manifest_entry)
        print(
            f"[ok] '{requested_title}' -> '{resolved_title}' "
            f"(rev {fetched['revision_id']}, {len(wikitext)} chars wikitext)"
        )

        time.sleep(SLEEP_S)

    conn.close()

    print(f"\nAdded {len(results)} page(s) this run; {len(failures)} failure(s).")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f['requested_title']}: {f['error']}")
    return results, failures


def sanity_queries():
    conn = sqlite3.connect(DB_PATH)
    queries = ["force bolt", "price 100 potion", "failure rate spell"]
    for q in queries:
        print(f"\n=== FTS5 query: {q!r} ===")
        rows = conn.execute(
            """
            SELECT p.page_title, bm25(pages_fts) AS rank
            FROM pages_fts
            JOIN pages p ON p.rowid = pages_fts.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT 3
            """,
            (q,),
        ).fetchall()
        for i, (title, rank) in enumerate(rows, 1):
            print(f"  {i}. {title}  (bm25={rank:.4f})")
        if not rows:
            print("  (no results)")
    conn.close()


if __name__ == "__main__":
    if "--sanity" in sys.argv:
        sanity_queries()
    else:
        _, failures = build()
        if failures:
            sys.exit(1)
        print("\nRunning sanity queries...")
        sanity_queries()
