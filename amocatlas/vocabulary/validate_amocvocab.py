"""Validate ``amocvocab.yml`` — the CI gate for the AMOC variable vocabulary.

The vocabulary is published and DOI'd for other groups to adopt, so an entry that
ships wrong propagates to everyone who cites it. This validator is the automated part
of the "ULTRA-CAREFUL" discipline: it runs the checks a human reviewer would otherwise
do by hand, and refuses the file if any fail.

Checks, in order:

1. **Schema** — the file validates against ``amocvocab.schema.json`` (JSON Schema
   draft 2020-12). This already enforces the conditional structure (``cf_status`` exact
   iff ``standard_name`` is a non-empty string; signed kinds require ``sign_convention``;
   non-current entries require ``superseded_by``; key/name patterns).
2. **name == key** — each quantity's ``name`` field equals its key. The schema checks
   both against the same pattern but cannot compare them to each other.
3. **Referential integrity** — every ``qualifiers`` code exists in the top-level
   ``qualifiers`` registry; every applied qualifier's class is admitted by the entry;
   every ``decomposition`` names a real decomposition whose ``of``/``components`` are real
   quantities; ``quantity`` (the base) and ``superseded_by`` name real quantities.
4. **CF name existence** — every non-null ``standard_name`` is a real ``<entry>`` or
   ``<alias>`` id in the CF standard-name table (never accepted from recall).
5. **Units** — every ``units`` and every ``units_alternatives`` entry parses under
   UDUNITS-2 (pyudunits2); ``units_alternatives`` are convertible to ``units``; and when
   a ``standard_name`` is set, ``units`` is convertible to that standard name's CF
   canonical units. This is the check that catches the freshwater-transport class of
   defect (sverdrup, a volume flux, is not convertible to CF's canonical kg s-1).

Exit status is 0 when clean, 1 when any check fails; each problem prints one line.

Run::

    python -m amocatlas.vocabulary.validate_amocvocab
    python -m amocatlas.vocabulary.validate_amocvocab --cf-table /path/to/cf-standard-name-table.xml
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_VOCAB = HERE / "amocvocab.yml"
DEFAULT_SCHEMA = HERE / "amocvocab.schema.json"
DEFAULT_CF_SUBSET = HERE / "cf_standard_names.json"
DEFAULT_DRAFT = HERE / "amocvocab_draft.yml"
DEFAULT_DRAFT_SCHEMA = HERE / "amocvocab_draft.schema.json"

# CF source search order: explicit arg > env > committed derived subset > /tmp XML cache.
# The committed JSON subset (build_cf_subset.py) is the reproducible default that CI reads,
# so a green build stays rebuildable; the XML forms are for the drift job and local use.
_CF_SOURCE_CANDIDATES = [
    DEFAULT_CF_SUBSET,
    HERE / "cf-standard-name-table.xml",
    Path("/tmp/cf-table.xml"),
]


def load_yaml(path: Path) -> dict:
    """Load a YAML file for validation (read-only; round-trip not needed)."""
    import yaml

    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_schema(path: Path) -> dict:
    """Load the JSON Schema document."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_cf_table(path: Path) -> tuple[dict[str, str], set[str]]:
    """Parse the CF standard-name table.

    Returns
    -------
    canonical_units : dict
        standard_name -> canonical units string (``""`` for dimensionless entries).
        Aliases resolve to their target entry's canonical units.
    valid_names : set
        All valid standard names: entry ids plus alias ids.

    """
    tree = ET.parse(path)
    root = tree.getroot()

    canonical: dict[str, str] = {}
    for entry in root.findall("entry"):
        name = entry.get("id")
        if name is None:
            continue
        cu = entry.findtext("canonical_units")
        canonical[name] = (cu or "").strip()

    aliases: dict[str, str] = {}
    for alias in root.findall("alias"):
        aid = alias.get("id")
        target = alias.findtext("entry_id")
        if aid and target:
            aliases[aid] = target.strip()

    # Resolve alias canonical units from their targets.
    for aid, target in aliases.items():
        if target in canonical:
            canonical[aid] = canonical[target]

    valid_names = set(canonical) | set(aliases)
    return canonical, valid_names


def load_cf_subset(path: Path) -> tuple[dict[str, str], set[str]]:
    """Load the committed CF subset JSON (built by build_cf_subset.py).

    Same return shape as ``load_cf_table``: a name -> canonical-units map (aliases
    resolved) and the set of all valid names (entry ids plus alias ids).
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    canonical: dict[str, str] = dict(data.get("entries") or {})
    aliases: dict[str, str] = dict(data.get("aliases") or {})
    for aid, target in aliases.items():
        if target in canonical:
            canonical[aid] = canonical[target]
    valid_names = set(canonical) | set(aliases)
    return canonical, valid_names


def load_cf_names(path: Path) -> tuple[dict[str, str], set[str]]:
    """Load CF names + canonical units from either the JSON subset or the XML table."""
    if str(path).endswith(".json"):
        return load_cf_subset(path)
    return load_cf_table(path)


def resolve_cf_table(explicit: str | None) -> Path:
    """Find a CF source (committed JSON subset by default), or raise with instructions."""
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise FileNotFoundError(f"CF source not found: {p}")
        return p
    env = os.environ.get("AMOCVOCAB_CF_TABLE")
    if env and Path(env).is_file():
        return Path(env)
    for cand in _CF_SOURCE_CANDIDATES:
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        "No CF source found. The committed subset "
        f"{DEFAULT_CF_SUBSET.name} should exist; regenerate it with "
        "`python -m amocatlas.vocabulary.build_cf_subset --xml <cf-table.xml>`, or pass "
        "--cf-table PATH / set AMOCVOCAB_CF_TABLE."
    )


# --- individual checks: each returns a list of human-readable problem strings ---


def schema_errors(vocab: dict, schema: dict) -> list[str]:
    """Validate against the JSON Schema; return one string per violation."""
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(vocab), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        out.append(f"schema: {loc}: {err.message}")
    return out


def name_key_errors(vocab: dict) -> list[str]:
    """Each quantity's ``name`` must equal its key."""
    out = []
    for key, entry in (vocab.get("quantities") or {}).items():
        name = entry.get("name")
        if name != key:
            out.append(f"name-key: quantity {key!r} has name {name!r} (must equal key)")
    return out


def referential_errors(vocab: dict) -> list[str]:
    """Cross-reference qualifiers, decompositions, base quantity, superseded_by."""
    out = []
    quantities = vocab.get("quantities") or {}
    qualifiers = vocab.get("qualifiers") or {}
    decompositions = vocab.get("decompositions") or {}
    q_keys = set(quantities)

    for key, entry in quantities.items():
        admits = set(entry.get("admits_qualifiers") or [])
        for code in entry.get("qualifiers") or []:
            if code not in qualifiers:
                out.append(
                    f"ref: quantity {key!r} uses qualifier {code!r} not in `qualifiers`"
                )
                continue
            cls = qualifiers[code].get("class")
            if admits and cls not in admits:
                out.append(
                    f"ref: quantity {key!r} applies qualifier {code!r} of class "
                    f"{cls!r}, which is not in its admits_qualifiers {sorted(admits)}"
                )

        base = entry.get("quantity")
        if base and base != key and base not in q_keys:
            out.append(
                f"ref: quantity {key!r} has base quantity {base!r} not in `quantities`"
            )

        dcp = entry.get("decomposition")
        if dcp and dcp not in decompositions:
            out.append(
                f"ref: quantity {key!r} names decomposition {dcp!r} not in "
                "`decompositions`"
            )

        sup = entry.get("superseded_by")
        if sup and sup not in q_keys:
            out.append(
                f"ref: quantity {key!r} superseded_by {sup!r} not in `quantities`"
            )

    for dkey, dec in decompositions.items():
        of = dec.get("of")
        if of and of not in q_keys:
            out.append(f"ref: decomposition {dkey!r} of {of!r} not in `quantities`")
        for comp in dec.get("components") or []:
            if comp not in q_keys:
                out.append(
                    f"ref: decomposition {dkey!r} component {comp!r} not in "
                    "`quantities`"
                )
    return out


def cf_name_errors(vocab: dict, valid_names: set[str]) -> list[str]:
    """Every non-null standard_name must exist in the CF table."""
    out = []
    for key, entry in (vocab.get("quantities") or {}).items():
        sn = entry.get("standard_name")
        if sn and sn not in valid_names:
            out.append(
                f"cf-name: quantity {key!r} standard_name {sn!r} is not a CF entry "
                "or alias (fabricated or misspelled)"
            )
    return out


def units_errors(vocab: dict, canonical: dict[str, str]) -> list[str]:
    """Units parse under UDUNITS-2 and are convertible where a standard_name is set."""
    from pyudunits2 import Unit, UnitSystem, UnresolvableUnitException

    us = UnitSystem.from_udunits2_xml()

    def parse(s: str) -> Unit:
        return us.unit(s)

    out = []
    for key, entry in (vocab.get("quantities") or {}).items():
        units = entry.get("units")
        u = None
        try:
            u = parse(units)
        except UnresolvableUnitException:
            out.append(
                f"units: quantity {key!r} units {units!r} do not parse under UDUNITS-2"
            )
        except Exception as exc:  # noqa: BLE001 - report any parser failure
            out.append(f"units: quantity {key!r} units {units!r} parse error: {exc}")

        for alt in entry.get("units_alternatives") or []:
            try:
                ua = parse(alt)
            except Exception:  # noqa: BLE001
                out.append(
                    f"units: quantity {key!r} alternative units {alt!r} do not parse"
                )
                continue
            if u is not None and not ua.is_convertible_to(u):
                out.append(
                    f"units: quantity {key!r} alternative {alt!r} is not convertible "
                    f"to units {units!r}"
                )

        sn = entry.get("standard_name")
        if sn and u is not None:
            cu = canonical.get(sn)
            if cu is None:
                # Missing from table is a CF-name problem, reported by cf_name_errors.
                continue
            target = cu if cu else "1"  # empty canonical_units == dimensionless
            try:
                tu = parse(target)
            except Exception:  # noqa: BLE001
                out.append(
                    f"units: CF canonical units {cu!r} for {sn!r} do not parse "
                    "(table issue)"
                )
                continue
            if not u.is_convertible_to(tu):
                out.append(
                    f"units: quantity {key!r} units {units!r} are not convertible to "
                    f"the CF canonical units {cu or '1'!r} of standard_name {sn!r}"
                )
    return out


def validate(vocab_path: Path, schema_path: Path, cf_table_path: Path) -> list[str]:
    """Run every check; return the combined list of problems (empty == valid)."""
    vocab = load_yaml(vocab_path)
    schema = load_schema(schema_path)
    canonical, valid_names = load_cf_names(cf_table_path)

    problems: list[str] = []
    # Schema first: later checks assume the structure it guarantees.
    problems += schema_errors(vocab, schema)
    if problems:
        return problems
    problems += name_key_errors(vocab)
    problems += referential_errors(vocab)
    problems += cf_name_errors(vocab, valid_names)
    problems += units_errors(vocab, canonical)
    return problems


def validate_draft(
    draft_path: Path,
    draft_schema_path: Path,
    strict_schema_path: Path,
    cf_table_path: Path,
) -> list[str]:
    """Validate the staging draft: loose overall, strict on every ``ready`` entry.

    Unreviewed/draft entries only have to satisfy the loose draft schema. Any entry marked
    ``ready`` must carry an ``entry`` that passes the FULL amocvocab checks (strict schema +
    name==key + CF-name existence + UDUNITS convertibility) — so nothing can be marked ready,
    and thus graduate into amocvocab.yml, while still broken.
    """
    draft = load_yaml(draft_path)
    draft_schema = load_schema(draft_schema_path)

    problems: list[str] = []
    problems += schema_errors(draft, draft_schema)
    if problems:
        return problems

    strict_schema = load_schema(strict_schema_path)
    canonical, valid_names = load_cf_names(cf_table_path)

    for key, item in (draft.get("quantities") or {}).items():
        if item.get("review_status") != "ready":
            continue
        entry = item.get("entry")
        if not entry:
            problems.append(f"{key}: review_status 'ready' but no 'entry' to graduate")
            continue
        # Re-use the published-vocab checks by wrapping the single entry in a mini vocab.
        # The synthetic version/table must themselves satisfy the strict top-level schema
        # (they are not what we are checking — the entry is).
        mini = {
            "version": "0.0",
            "cf_standard_name_table": "draft",
            "quantities": {key: entry},
        }
        problems += [f"{key}.entry: {p}" for p in schema_errors(mini, strict_schema)]
        problems += [f"{key}.entry: {p}" for p in name_key_errors(mini)]
        problems += [f"{key}.entry: {p}" for p in cf_name_errors(mini, valid_names)]
        problems += [f"{key}.entry: {p}" for p in units_errors(mini, canonical)]
    return problems


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit status."""
    ap = argparse.ArgumentParser(description="Validate the amocvocab vocabulary file.")
    ap.add_argument("--vocab", default=str(DEFAULT_VOCAB), help="Path to amocvocab.yml")
    ap.add_argument(
        "--schema", default=str(DEFAULT_SCHEMA), help="Path to amocvocab.schema.json"
    )
    ap.add_argument(
        "--cf-table",
        default=None,
        help="Path to a CF source (JSON subset or XML table); "
        "defaults to the committed cf_standard_names.json.",
    )
    ap.add_argument(
        "--draft",
        nargs="?",
        const=str(DEFAULT_DRAFT),
        default=None,
        help="Validate the staging draft (loose overall, strict on 'ready' entries) "
        "instead of the published vocab. Optional path; defaults to amocvocab_draft.yml.",
    )
    args = ap.parse_args(argv)

    try:
        cf_table = resolve_cf_table(args.cf_table)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.draft is not None:
        problems = validate_draft(
            Path(args.draft), DEFAULT_DRAFT_SCHEMA, Path(args.schema), cf_table
        )
        label = f"amocvocab draft ({args.draft})"
    else:
        problems = validate(Path(args.vocab), Path(args.schema), cf_table)
        label = "amocvocab"

    if problems:
        print(f"{label}: {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"{label}: OK (CF table: {cf_table})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
