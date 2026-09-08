"""Derive the committed CF subset that the amocvocab validator reads.

The validator only needs, per CF standard name: whether it exists, and its canonical
units. That is a few hundred KB — not the 4.5 MB source XML. This script derives that
subset (``cf_standard_names.json``) from the full table, so the repo pins a *reproducible*
artifact: a green build stays rebuildable, and ``amocvocab.yml``'s
``cf_standard_name_table: "v94 (2026-06-09)"`` claim is verifiable against a committed
file rather than against whatever is live today.

Regenerate only on a deliberate CF-table bump (the scheduled drift job flags when the live
table has moved on)::

    python -m amocatlas.vocabulary.build_cf_subset --xml /tmp/cf-table.xml

Download the source table from
https://cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-table.xml
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SUBSET = HERE / "cf_standard_names.json"
SOURCE_URL = (
    "https://cfconventions.org/Data/cf-standard-names/current/src/"
    "cf-standard-name-table.xml"
)


def derive(xml_path: Path) -> dict:
    """Parse the CF table XML into the committed subset dict."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    version = (root.findtext("version_number") or "").strip()
    last_modified = (root.findtext("last_modified") or "").strip()
    date = last_modified.split("T")[0] if last_modified else ""
    label = f"v{version} ({date})" if version and date else (version or "unknown")

    entries = {}
    for entry in root.findall("entry"):
        eid = entry.get("id")
        if eid is None:
            continue
        entries[eid] = (entry.findtext("canonical_units") or "").strip()

    aliases = {}
    for alias in root.findall("alias"):
        aid = alias.get("id")
        target = alias.findtext("entry_id")
        if aid and target:
            aliases[aid] = target.strip()

    return {
        "label": label,
        "version": version,
        "last_modified": date,
        "source": SOURCE_URL,
        "entry_count": len(entries),
        "alias_count": len(aliases),
        # Sorted for reproducible, reviewable diffs.
        "entries": dict(sorted(entries.items())),
        "aliases": dict(sorted(aliases.items())),
    }


def write_subset(subset: dict, out_path: Path = DEFAULT_SUBSET) -> None:
    """Write the subset as sorted JSON with a trailing newline."""
    out_path.write_text(
        json.dumps(subset, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main(argv: list | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Derive the committed CF subset.")
    ap.add_argument("--xml", required=True, help="Path to cf-standard-name-table.xml")
    ap.add_argument("--out", default=str(DEFAULT_SUBSET), help="Output JSON path")
    args = ap.parse_args(argv)

    xml_path = Path(args.xml)
    if not xml_path.is_file():
        print(f"ERROR: XML not found: {xml_path}", file=sys.stderr)
        return 2
    subset = derive(xml_path)
    write_subset(subset, Path(args.out))
    print(
        f"wrote {args.out}: {subset['label']}, "
        f"{subset['entry_count']} entries + {subset['alias_count']} aliases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
