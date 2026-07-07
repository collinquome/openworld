# NH-E13 knowledge base — resource-constrained + reproducible (operator spec)

- Consulted wiki pages are snapshotted into a LOCAL corpus: `wiki_kb.sqlite`
  (SQLite FTS5 — T312 benchmarked FTS5 as the retrieval winner at our scale)
  plus `wiki_kb_manifest.json`: {page, url, revision date, sha256, added_by,
  added_when, reason}.
- Experiments query the LOCAL KB only. Live WebFetch is allowed solely to ADD
  pages to the KB (logged in the manifest) — never ad-hoc mid-experiment reads.
  This freezes the knowledge corpus per experiment: "do strategy guides help"
  becomes a controlled, versioned, reproducible comparison.
- Retrieval calls from Arm B / Mode-B consultations log: query, pages hit,
  advice extracted, whether the objective stack changed.
