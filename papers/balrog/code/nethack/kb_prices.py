"""NH-E18 price-ID reference: parse base-cost tables out of the NH-E13
wiki KB wikitext (provenance: wiki, revision ids in wiki_kb_manifest.json).

MODEL: Fable 5 (max reasoning), Phase L session 1.
Layer: MEMORY (reference table consumed by the INTUITION dot-connector).

Output: results/kb_prices.json
  {class: {cost: [ {name, prob, appearance_fixed} ... ]}}
The dot-connector inference: (observed price, item class) -> candidate
identity set = table[class][base_cost_consistent_with_price]. Buy price
includes charisma multiplier + 33% unidentified surcharge (wiki: Price
identification); sell price = base/2 (±25% sucker rule) — candidate match
must account for both channels.
"""

import json
import re
import sqlite3

POTION_ROW = re.compile(
    r"\{\{of\|potion\|([a-z' -]+)\}\}[^|]*\|\|\s*(\d+)\s*\|\|"
    r"\s*\d+\s*\|\|\s*([\d.]+)%?", re.I)
SCROLL_ROW = re.compile(
    r"\[\[scroll of [a-z' -]+\|([a-z' -]+)\]\]\s*\|\|\s*(\d+)\s*\|\|"
    r"\s*([\d.]+)%", re.I)
WAND_ROW = re.compile(
    r"\[\[wand of [a-z' -]+\|([a-z' -]+)\]\]\n\|(\d+)\n"
    r"\|[^\n]*\n\|([\d.]+)%\n\|(?:'')?([a-z -]+?)(?:'')?\n", re.I)
RING_ROW = re.compile(
    r"\[\[ring of ([a-z' -]+)\]\]\s*\|\|\s*(\d+)\s*\|\|", re.I)


def main():
    db = sqlite3.connect("wiki_kb.sqlite")
    out = {}

    def grab(cls, page, rx, extra=None):
        row = db.execute(
            "select wikitext from pages where page_title=?", (page,)
        ).fetchone()
        if not row:
            return
        table = {}
        wand_types = {}
        for m in rx.finditer(row[0]):
            name, cost = m.group(1).strip(), int(m.group(2))
            item = {"name": name}
            if rx in (POTION_ROW, SCROLL_ROW, WAND_ROW):
                item["prob"] = float(m.group(3))
            if rx is WAND_ROW:
                item["type"] = m.group(4).strip()
                wand_types[name] = item["type"]
            table.setdefault(cost, []).append(item)
        if table:
            out[cls] = {str(k): v for k, v in sorted(table.items())}
        if wand_types:
            out["wand_types"] = wand_types

    grab("potion", "Potion", POTION_ROW)
    grab("scroll", "Scroll", SCROLL_ROW)
    grab("wand", "Wand", WAND_ROW)
    grab("ring", "Ring", RING_ROW)
    with open("results/kb_prices.json", "w") as f:
        json.dump(out, f, indent=1)
    for cls, t in out.items():
        if cls == "wand_types":
            print(f"wand_types: {len(t)}")
            continue
        n = sum(len(v) for v in t.values())
        print(f"{cls}: {n} items across {len(t)} price points")


if __name__ == "__main__":
    main()
