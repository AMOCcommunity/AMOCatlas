"""Scan the per-array metadata YAMLs and inventory every standardised variable.

The metadata YAMLs under ``amocatlas/metadata/`` are the ground truth for what
AMOCatlas actually serves: each ``files.<file>.variable_mapping`` maps a provider
variable name to a standardised short name, and ``original_variable_metadata`` carries
the verified ``standard_name``/``units``/``long_name`` for that provider variable.

This module gathers those into a per-short-name inventory so the vocabulary can be
populated from what is served rather than from recall, and so conflicts (one short name
served with two different standard_names or units) surface explicitly.

It reads only; it does not write or fabricate.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
METADATA_DIR = HERE.parent / "metadata"
DEFAULT_DRAFT = HERE / "amocvocab_draft.yml"
DEFAULT_VOCAB = HERE / "amocvocab.yml"

# _ERR/_QC variants inherit their base quantity's vocab entry; they are not themselves
# vocabulary quantities (the amocvocab schema forbids these suffixes as keys), so they are
# excluded from the draft.
_RESERVED_SUFFIX = re.compile(r"_(ERR|QC)$")

# Registry/schema files under metadata/ that are not per-array YAMLs.
_NON_ARRAY = {
    "contributor_registry.yml",
    "institution_registry.yml",
    "array_schema.json",
}


@dataclass
class Occurrence:
    """One appearance of a standardised short name in a source file."""

    array: str
    source_file: str
    original_name: str
    standard_name: str | None
    units: str | None
    long_name: str | None
    description: str | None


@dataclass
class ShortName:
    """All occurrences of one standardised short name across arrays."""

    name: str
    occurrences: list[Occurrence] = field(default_factory=list)

    @property
    def standard_names(self) -> set:
        """Distinct standard_names this short name is served with."""
        return {o.standard_name for o in self.occurrences}

    @property
    def units(self) -> set:
        """Distinct units this short name is served with."""
        return {o.units for o in self.occurrences}

    @property
    def arrays(self) -> set:
        """Arrays that serve this short name."""
        return {o.array for o in self.occurrences}

    @property
    def has_conflict(self) -> bool:
        """True if this name is served with more than one standard_name or unit."""
        sn = {s for s in self.standard_names if s}
        un = {u for u in self.units if u}
        return len(sn) > 1 or len(un) > 1


def _iter_array_yaml(metadata_dir: Path) -> Iterator[Path]:
    for path in sorted(metadata_dir.glob("*.yml")):
        if path.name in _NON_ARRAY:
            continue
        yield path


def build_inventory(metadata_dir: Path = METADATA_DIR) -> dict[str, ShortName]:
    """Return {short_name: ShortName} across all per-array metadata YAMLs."""
    import yaml

    from ..utilities import sanitize_variable_name

    result: dict[str, ShortName] = {}

    for path in _iter_array_yaml(metadata_dir):
        array = path.stem
        with open(path, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        files = doc.get("files") or {}
        for source_file, spec in files.items():
            if not isinstance(spec, dict):
                continue
            mapping = spec.get("variable_mapping") or {}
            ovm = spec.get("original_variable_metadata") or {}
            for original_name, short in mapping.items():
                if not isinstance(short, str):
                    continue
                # variable_mapping keys are raw provider names; original_variable_metadata
                # keys are sanitised (the reader matches them the same way), so fall back to
                # the sanitised key when the raw one misses.
                meta = ovm.get(original_name)
                if meta is None:
                    meta = ovm.get(sanitize_variable_name(original_name))
                meta = meta or {}
                occ = Occurrence(
                    array=array,
                    source_file=source_file,
                    original_name=original_name,
                    standard_name=meta.get("standard_name"),
                    units=meta.get("units"),
                    long_name=meta.get("long_name"),
                    description=meta.get("description"),
                )
                result.setdefault(short, ShortName(name=short)).occurrences.append(occ)

    return dict(sorted(result.items()))


def summarize(inventory: dict[str, ShortName]) -> str:
    """Human-readable summary: names, their standard_names/units, and conflicts."""
    lines = [f"{len(inventory)} standardised short names across the arrays.", ""]
    conflicts = [n for n in inventory.values() if n.has_conflict]
    lines.append(f"{len(conflicts)} served with conflicting standard_name or units:")
    for sn in conflicts:
        lines.append(f"  {sn.name}:")
        lines.append(
            f"    standard_names: {sorted(s or '-' for s in sn.standard_names)}"
        )
        lines.append(f"    units:          {sorted(u or '-' for u in sn.units)}")
        lines.append(f"    arrays:         {sorted(sn.arrays)}")
    return "\n".join(lines)


def _sorted_distinct(values: set) -> list:
    """Sort a set that may contain None (None sorts last)."""
    return sorted(values, key=lambda x: (x is None, x or ""))


def _observed_block(sn: ShortName) -> dict:
    """The observed per-array state for a short name (refreshed from inventory)."""
    return {
        "standard_names": _sorted_distinct(sn.standard_names),
        "units": _sorted_distinct(sn.units),
        "conflict": sn.has_conflict,
    }


def _published_names(vocab_path: Path = DEFAULT_VOCAB) -> set:
    """Short names already published in amocvocab.yml (seeded as review_status ready)."""
    import yaml

    if not vocab_path.is_file():
        return set()
    with open(vocab_path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    return set((doc.get("quantities") or {}).keys())


def seed_draft(
    existing: dict | None = None,
    metadata_dir: Path = METADATA_DIR,
    vocab_path: Path = DEFAULT_VOCAB,
) -> dict:
    """Return an amocvocab draft seeded from the served-name inventory.

    Every standardised short name (except ``_ERR``/``_QC`` variants) becomes a draft entry.
    Names already in ``amocvocab.yml`` are seeded ``published`` (they live there, not here);
    the rest ``unreviewed``. The ``served_by``/``observed`` fields are refreshed from the
    inventory on every call; hand-edited ``review_status``/``notes``/``entry`` on existing
    entries are preserved.
    """
    inv = build_inventory(metadata_dir)
    published = _published_names(vocab_path)

    draft = existing or {
        "version": "0.1-draft",
        "description": (
            "Working superset of amocvocab. NOT published. Entries graduate into "
            "amocvocab.yml when review_status is 'ready'."
        ),
        "generated_from": "inventory of amocatlas/metadata",
        "quantities": {},
    }
    quantities = draft.setdefault("quantities", {})

    for name, sn in inv.items():
        if _RESERVED_SUFFIX.search(name):
            continue
        if name in quantities:
            # Preserve decisions; refresh only the observed-from-arrays fields.
            quantities[name]["served_by"] = sorted(sn.arrays)
            quantities[name]["observed"] = _observed_block(sn)
            continue
        quantities[name] = {
            "review_status": "published" if name in published else "unreviewed",
            "served_by": sorted(sn.arrays),
            "observed": _observed_block(sn),
            "notes": "",
            "entry": None,
        }

    # Sort entries by name for a stable, reviewable file.
    draft["quantities"] = {k: quantities[k] for k in sorted(quantities)}
    return draft


def seed_draft_file(
    draft_path: Path = DEFAULT_DRAFT,
    metadata_dir: Path = METADATA_DIR,
    vocab_path: Path = DEFAULT_VOCAB,
) -> int:
    """Seed/refresh the draft YAML on disk. Returns the number of quantities."""
    import yaml

    existing = None
    if draft_path.is_file():
        with open(draft_path, encoding="utf-8") as fh:
            existing = yaml.safe_load(fh)
    draft = seed_draft(existing, metadata_dir, vocab_path)
    with open(draft_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(
            draft,
            fh,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=100,
        )
    return len(draft["quantities"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "seed-draft":
        n = seed_draft_file()
        print(f"seeded {n} quantities into {DEFAULT_DRAFT}")
    else:
        print(summarize(build_inventory()))
