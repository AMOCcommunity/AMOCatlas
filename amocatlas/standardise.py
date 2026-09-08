"""Standardisation functions for AMOC observing array datasets.

These functions take raw loaded datasets and:
- Rename variables to standard names
- Add variable-level metadata
- Add or update global attributes
- Prepare datasets for downstream analysis

Currently implemented:
- SAMBA
"""

import os
import re
import warnings
from collections import OrderedDict
from datetime import datetime, timezone

import xarray as xr

from amocatlas import contributors, defaults, logger, utilities
from amocatlas.logger import log_debug

log = logger.log  # Use the global logger

# Extracted from OG1.0 spec “## Global attributes” (cf. turn1view0) :contentReference[oaicite:0]{index=0}
_GLOBAL_ATTR_ORDER = defaults.GLOBAL_ATTR_ORDER

# Institution corrections are now handled in contributors.py


def reorder_metadata(attrs: dict) -> dict:
    """Return a new dict with keys ordered according to the OG1.0 global‐attribute list.
    Any attrs not in the spec list are appended at the end, in their original order.
    """
    # Shallow copy so we can pop
    remaining = dict(attrs)
    ordered = OrderedDict()

    for key in _GLOBAL_ATTR_ORDER:
        # Some attributes are case-sensitive and must match exactly
        if key in ["Conventions", "featureType", "featureType_vocabulary"]:
            if key in remaining:
                ordered[key] = remaining.pop(key)
        else:
            # look for any remaining key whose lower() matches
            to_remove = None
            for orig in remaining:
                if orig.lower() == key.lower():
                    to_remove = orig
                    break
            if to_remove is not None:
                ordered[to_remove] = remaining.pop(to_remove)

    # finally, append all the rest in their original insertion order
    for orig, val in remaining.items():
        ordered[orig] = val

    return dict(ordered)


def normalize_and_add_vocabulary(
    attrs: dict, normalizations: dict[str, tuple[dict[str, str], str]]
) -> dict:
    """For each (attr, (value_map, vocab_url)) in `normalizations`.

      - If `attr` exists in attrs:
          * Map attrs[attr] using value_map (or leave it if unmapped)
          * Add attrs[f"{attr}_vocabulary"] = vocab_url

    Parameters
    ----------
    attrs : dict
        Metadata attributes, already cleaned & renamed.
    normalizations : dict
        Keys are canonical attr names (e.g. "platform"), values are
        (value_map, vocabulary_url) tuples.

    Returns
    -------
    dict
        attrs with normalized values and added <attr>_vocabulary entries.

    """
    for attr, (value_map, vocab_url) in normalizations.items():
        if attr in attrs:
            raw = attrs[attr]
            mapped = value_map.get(raw, raw)
            if mapped != raw:
                log_debug("Normalized '%s': %r → %r", attr, raw, mapped)
            attrs[attr] = mapped

            vocab_key = f"{attr}_vocabulary"
            # only set if not already present
            if vocab_key not in attrs:
                attrs[vocab_key] = vocab_url
                log_debug("Added vocabulary for '%s': %s", attr, vocab_url)

    return attrs


def get_dynamic_version() -> str:
    """Get the actual software version using multiple detection methods.

    Priority:
    1. Git describe (for development in git repo)
    2. Installed package version (for pip/conda installs)
    3. Fallback to __version__ file

    Returns
    -------
    str
        Software version string

    """
    import os
    import subprocess

    # Method 1: Try git describe for development versions
    try:
        # Get the directory of this file to find git repo root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(current_dir)  # Go up from amocatlas/ to repo root

        result = subprocess.run(
            ["git", "describe", "--tags", "--dirty", "--always"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_version = result.stdout.strip()

            # Strip everything after vX.X.X pattern (remove commit info and dirty flag)

            version_match = re.match(r"(v?\d+\.\d+\.\d+)", git_version)
            if version_match:
                clean_version = version_match.group(1)
                log_debug(
                    f"Using cleaned git version: {clean_version} (from {git_version})"
                )
                return clean_version

            log_debug(f"Using git version: {git_version}")
            return git_version
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        # Git not available or repository not found
        pass

    # Method 2: Try installed package version
    try:
        import importlib.metadata

        installed_version = importlib.metadata.version("amocatlas")
    except (importlib.metadata.PackageNotFoundError, ImportError):
        pass
    else:
        log_debug(f"Using installed package version: {installed_version}")
        return installed_version

    # Method 3: Fallback to __version__ file
    from amocatlas._version import __version__

    log_debug(f"Using fallback version from __version__: {__version__}")
    return __version__


_NUMERIC_CONFLICT_KEYS = {
    "geospatial_lat_min",
    "geospatial_lat_max",
    "geospatial_lon_min",
    "geospatial_lon_max",
    "geospatial_vertical_min",
    "geospatial_vertical_max",
}

_DATE_CONFLICT_KEYS = {
    "time_coverage_start",
    "time_coverage_end",
    "start_date",
    "date_created",
    "date_modified",
    "creation_date",
    "processing_date",
}

_IDENTIFIER_CONFLICT_KEYS = {"doi", "id", "uuid", "uri", "contributor_id", "license"}
_IDENTIFIER_CONFLICT_SUFFIXES = ("_url", "_id", "_doi", "_vocabulary")


def _classify_conflict_field(key: str) -> str:
    """Classify a metadata key for conflict resolution.

    Returns one of ``"number"``, ``"date"``, ``"identifier"`` or ``"text"``. Typed
    fields are resolved by value equivalence and source priority, never by string
    length (which let a wrong-hemisphere latitude win because the minus sign made the
    string longer).

    Matching uses explicit key sets and underscore-delimited suffixes rather than bare
    substrings, so keys like ``update_interval`` (which contains ``"date"``) are not
    misclassified.
    """
    k = key.lower()
    if key in _NUMERIC_CONFLICT_KEYS or k.startswith("geospatial_"):
        return "number"
    if k in _DATE_CONFLICT_KEYS or k.endswith("_date") or k.startswith("date_"):
        return "date"
    if k in _IDENTIFIER_CONFLICT_KEYS or k.endswith(_IDENTIFIER_CONFLICT_SUFFIXES):
        return "identifier"
    return "text"


def _typed_values_equivalent(field_type: str, first: str, second: str) -> bool:
    """Return True if two typed values are equivalent despite differing text."""
    if field_type == "number":
        try:
            return float(first) == float(second)
        except (TypeError, ValueError):
            return False
    if field_type == "date":
        try:
            import pandas as pd

            a, b = pd.to_datetime(first), pd.to_datetime(second)
            # A tz-naive and a tz-aware timestamp compare unequal (or raise), so
            # '1995-11-13' would spuriously conflict with '1995-11-13T00:00:00Z'.
            # Treat a naive value as UTC so same-instant, differently-formatted dates match.
            if (a.tzinfo is None) != (b.tzinfo is None):
                if a.tzinfo is None:
                    a = a.tz_localize("UTC")
                else:
                    b = b.tz_localize("UTC")
        except (TypeError, ValueError):
            return first == second
        else:
            # Compare at day granularity: a nominal YAML date ('2021-08-07', day precision)
            # agrees with the file's precise timestamp on the same day
            # ('2021-08-07T17:00:00Z'). A different calendar day is still a real conflict.
            return a.normalize() == b.normalize()
    # identifiers are only equivalent when the strings match exactly, which the caller
    # has already ruled out by the time this is reached.
    return False


# time_coverage is derived from the TIME coordinate, not merged from nominal YAML/file
# attributes (which are often wrong by days). These keys are skipped in the YAML merge.
_TIME_COVERAGE_KEYS = ("time_coverage_start", "time_coverage_end")


def _time_coverage_from_data(ds: xr.Dataset) -> "tuple[str | None, str | None]":
    """Return (start, end) as ISO-8601 'Z' strings from the TIME coordinate.

    time_coverage should describe the actual served data, so it is computed from the
    standardized TIME coordinate rather than trusted from nominal YAML/file attributes.
    Returns (None, None) if there is no usable datetime TIME.
    """
    import numpy as np

    for tname in ("TIME", "time"):
        if tname in ds.variables:
            t = np.asarray(ds[tname].values)
            if np.issubdtype(t.dtype, np.datetime64):
                t = t[~np.isnat(t)]
                if t.size:
                    return (
                        np.datetime_as_string(t.min(), unit="s") + "Z",
                        np.datetime_as_string(t.max(), unit="s") + "Z",
                    )
    return None, None


def _warn_metadata_conflict(
    key: str,
    existing_str: str,
    new_str: str,
    existing_source: str,
    new_source: str,
    resolution: str,
) -> None:
    """Log the full conflict detail and emit a user-visible warning."""

    def _trunc(value: str) -> str:
        return f"{value[:100]}{'...' if len(value) > 100 else ''} ({len(value)} chars)"

    log_debug(
        f"METADATA CONFLICT for '{key}':\n"
        f"  Option 1 ({existing_source}): {_trunc(existing_str)}\n"
        f"  Option 2 ({new_source}): {_trunc(new_str)}\n"
        f"  → {resolution}"
    )
    warnings.warn(
        f"Metadata conflict for '{key}': {existing_source}={existing_str!r} vs "
        f"{new_source}={new_str!r}; {resolution}.",
        stacklevel=3,
    )


def resolve_metadata_conflict(
    key: str,
    existing_value: str,
    new_value: str,
    existing_source: str = "unknown",
    new_source: str = "unknown",
) -> str:
    """Resolve metadata conflicts using field-typed logic.

    Resolution rules:

    1. If values are identical, return without warning
    2. If one is empty/whitespace and other isn't, use non-empty
    3. For typed fields (numbers, dates, identifiers): keep the source-of-truth
       (existing) value and warn if the values genuinely differ; never compare by length
    4. For free text: keep the longer value (logged, not warned, to avoid noise)

    Parameters
    ----------
    key : str
        Metadata key name
    existing_value : str
        Current value
    new_value : str
        New value attempting to override
    existing_source : str
        Description of where existing value came from
    new_source : str
        Description of where new value came from

    Returns
    -------
    str
        The resolved value to use

    """
    # Convert to strings for comparison
    existing_str = str(existing_value).strip()
    new_str = str(new_value).strip()

    # If identical, no conflict
    if existing_str == new_str:
        log_debug(f"'{key}': identical values, no conflict")
        return existing_value

    # If one is empty, use the non-empty one
    if not existing_str and new_str:
        log_debug(f"'{key}': using non-empty value from {new_source}")
        return new_value
    if existing_str and not new_str:
        log_debug(f"'{key}': keeping existing non-empty value from {existing_source}")
        return existing_value

    # Both are non-empty but different - resolve by field type.
    field_type = _classify_conflict_field(key)

    if field_type in ("number", "date", "identifier"):
        if _typed_values_equivalent(field_type, existing_str, new_str):
            log_debug(f"'{key}': equivalent {field_type} values, keeping existing")
            return existing_value
        _warn_metadata_conflict(
            key,
            existing_str,
            new_str,
            existing_source,
            new_source,
            resolution=f"keeping {existing_source} ({field_type} mismatch)",
        )
        return existing_value

    # Free text: keep the longer value. Logged (not warned) to avoid noise, since
    # array-level YAML routinely provides longer descriptions than the source file.
    existing_len = len(existing_str)
    new_len = len(new_str)
    if new_len > existing_len:
        log_debug(
            f"METADATA CONFLICT for '{key}':\n"
            f"  Option 1 ({existing_source}): {existing_str[:100]}{'...' if existing_len > 100 else ''} ({existing_len} chars)\n"
            f"  Option 2 ({new_source}): {new_str[:100]}{'...' if new_len > 100 else ''} ({new_len} chars)\n"
            f"  → Using Option 2 (longer value)"
        )
        return new_value
    log_debug(
        f"METADATA CONFLICT for '{key}':\n"
        f"  Option 1 ({existing_source}): {existing_str[:100]}{'...' if existing_len > 100 else ''} ({existing_len} chars)\n"
        f"  Option 2 ({new_source}): {new_str[:100]}{'...' if new_len > 100 else ''} ({new_len} chars)\n"
        f"  → Using Option 1 (longer/equal value)"
    )
    return existing_value


def _normalize_contributor_ids(cleaned: dict) -> None:
    """Normalise contributor_id values to full dereferenceable URLs, in place.

    A bare ORCID (``0000-0001-2345-6789``) becomes ``https://orcid.org/…`` and a bare web
    address (``www.example.org``) gets an ``https://`` scheme. Values already starting with a
    scheme, and empty placeholders (which keep the list aligned with names), are unchanged.
    """
    raw = str(cleaned.get("contributor_id", ""))
    if not raw.strip():
        return
    orcid = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
    out = []
    changed = False
    for v in [x.strip() for x in raw.split(",")]:
        if not v or v.startswith(("http://", "https://")):
            out.append(v)
        elif orcid.match(v):
            out.append("https://orcid.org/" + v)
            changed = True
        elif "." in v and " " not in v:  # a bare web address, e.g. www.npolar.no
            out.append("https://" + v)
            changed = True
        else:
            out.append(v)
    if changed:
        cleaned["contributor_id"] = ", ".join(out)


def _backfill_contributor_email_by_id(cleaned: dict) -> None:
    """Propagate a contributor's email to every row sharing the same ORCID, in place.

    A person may appear under several distinct roles (originator + principalInvestigator),
    with the email present on only one row. Once ids are resolved, fill any empty
    contributor_email whose row has an ORCID that another row supplied an email for.
    contributor_id and contributor_email stay aligned (same length).
    """
    ids = [s.strip() for s in str(cleaned.get("contributor_id", "")).split(",")]
    emails = [s.strip() for s in str(cleaned.get("contributor_email", "")).split(",")]
    if not any(ids) or len(ids) != len(emails):
        return
    email_by_id: dict = {}
    for cid, email in zip(ids, emails, strict=False):
        if cid and email:
            email_by_id.setdefault(cid, email)
    changed = False
    for i, (cid, email) in enumerate(zip(ids, emails, strict=False)):
        if cid and not email and cid in email_by_id:
            emails[i] = email_by_id[cid]
            changed = True
    if changed:
        cleaned["contributor_email"] = ", ".join(emails)


def _dedup_institution_metadata(cleaned: dict) -> None:
    """Deduplicate the parallel contributing-institution lists in place.

    Like contributors, an institution may legitimately appear once per DISTINCT role, but
    should not be listed twice with the same or an empty role (e.g. a source that lists an
    institution as both publisher and an unroled contributor). Keeps the first (name, role),
    fills an empty vocabulary from a duplicate, and drops a bare empty-role entry when the
    same institution already carries a real role. Institution/vocabulary/role stay aligned.
    """
    names = [
        s.strip() for s in str(cleaned.get("contributing_institutions", "")).split(",")
    ]
    if not any(names):
        return
    vocabs = [
        s.strip()
        for s in str(cleaned.get("contributing_institutions_vocabulary", "")).split(",")
    ]
    roles = [
        s.strip()
        for s in str(cleaned.get("contributing_institutions_role", "")).split(",")
    ]
    vocabs += [""] * (len(names) - len(vocabs))
    roles += [""] * (len(names) - len(roles))

    deduped: dict = {}
    for name, vocab, role in zip(names, vocabs, roles, strict=False):
        if not name:
            continue
        key = (name.lower(), role)
        if key in deduped:
            if not deduped[key]["vocab"] and vocab:
                deduped[key]["vocab"] = vocab
        else:
            deduped[key] = {"name": name, "vocab": vocab, "role": role}

    named_with_role = {nk for (nk, role) in deduped if role}
    kept = [v for (nk, role), v in deduped.items() if role or nk not in named_with_role]

    cleaned["contributing_institutions"] = ", ".join(x["name"] for x in kept)
    cleaned["contributing_institutions_vocabulary"] = ", ".join(
        x["vocab"] for x in kept
    )
    cleaned["contributing_institutions_role"] = ", ".join(x["role"] for x in kept)


def clean_metadata(attrs: dict, preferred_keys: dict = None) -> dict:
    """Clean up a metadata dictionary.

    - Normalize key casing
    - Merge aliases with identical values
    - Apply standard naming (via preferred_keys mapping)
    """
    # Step 0: normalize whitespace everywhere
    attrs = utilities.normalize_whitespace(attrs)

    if preferred_keys is None:
        preferred_keys = defaults.METADATA_KEY_MAPPINGS

    # Step 1: merge any identical aliases first
    merged_attrs = merge_metadata_aliases(attrs, preferred_keys)

    # Step 2: normalize remaining cases and resolve conflicts
    cleaned = {}
    for key, value in merged_attrs.items():
        # key is already canonical if it was an alias
        if key in cleaned:
            # Use centralized conflict resolution
            resolved_value = resolve_metadata_conflict(
                key, cleaned[key], value, "merged metadata", "alias consolidation"
            )
            cleaned[key] = resolved_value
        else:
            cleaned[key] = value

    # Step 3: consolidate contributors and institutions
    cleaned = _consolidate_contributors(cleaned)
    return cleaned


def _standardize_role_names(role_string: str, role_map: dict) -> str:
    """Standardize individual role names in a comma-separated role string.

    Args:
        role_string: Comma-separated string of role names
        role_map: Dictionary mapping role names to standard NERC G04 terms

    Returns
    -------
        Standardized comma-separated role string

    """
    if not role_string or not role_string.strip():
        return role_string

    roles = [role.strip() for role in role_string.split(",")]
    standardized_roles = []

    for role in roles:
        if not role:  # Skip empty roles
            standardized_roles.append("")
            continue

        # Apply role mapping if available
        standardized_role = role_map.get(role, role)
        standardized_roles.append(standardized_role)

    return ", ".join(standardized_roles)


def _consolidate_contributors(cleaned: dict) -> dict:
    """Consolidate creators, PIs, publishers, and contributors into unified fields.

    Uses the new modular contributor functions from contributors.py for enhanced
    ORCID lookup and name standardization.

    These include:
    - contributor_name, contributor_role, contributor_email, contributor_id aligned one-to-one
    - contributing_institutions, with placeholders for vocabularies/roles
    """
    log_debug("Starting _consolidate_contributors with attrs: %s", cleaned)

    role_map = defaults.CONTRIBUTOR_ROLE_MAP

    # Step A: Extract and consolidate contributor fields using new modular approach
    # Collect all contributor-related fields from various sources
    raw_names = []
    raw_roles = []
    raw_emails = []
    raw_ids = []

    # Process each contributor category into dictionaries, then combine
    all_contributors = {}
    current_index = 1

    # Phase 1: Process role-specific fields first (creator, PI, publisher)
    role_priority_fields = ["creator_name", "principal_investigator", "publisher_name"]

    for key in role_priority_fields:
        if key in cleaned:
            # Derive the sibling field prefix. "creator_name"/"publisher_name" -> "creator"
            # /"publisher"; "principal_investigator" has no "_name" suffix and is its own base.
            base = key[:-5] if key.endswith("_name") else key
            name_raw = cleaned.pop(key, "")
            email_raw = cleaned.pop(f"{base}_email", "")
            id_raw = cleaned.pop(f"{base}_id", "")
            url_raw = cleaned.pop(f"{base}_url", "")
            role_value = role_map.get(key, "")

            # Prefer a real identifier (e.g. ORCID); fall back to a profile URL only when no
            # id is given (matches the registry's id_url convention). Previously the URL was
            # passed as the id, which put webpages in contributor_id and left creator_id /
            # principal_investigator_id leaking into the output as stray attributes.
            category_dict = contributors.parse_contributors(
                name_raw, id_raw or url_raw, email_raw, role_value
            )

            # Add to combined dict with sequential indices
            for contributor in category_dict.values():
                if contributor["name"]:  # Only add non-empty names
                    all_contributors[str(current_index)] = contributor
                    current_index += 1

    # Phase 2: Process any remaining role-mapped fields (except contributor_name)
    for key in list(cleaned.keys()):
        if key in role_map and key != "contributor_name":
            raw = cleaned.pop(key)
            role_value = role_map[key]

            # Process as single-role category
            category_dict = contributors.parse_contributors(raw, "", "", role_value)

            # Add to combined dict with sequential indices
            for contributor in category_dict.values():
                if contributor["name"]:
                    all_contributors[str(current_index)] = contributor
                    current_index += 1

    # Phase 3: Process contributor_name and related fields LAST
    explicit_contributor_role = cleaned.pop("contributor_role", "")

    if "contributor_name" in cleaned:
        name_raw = cleaned.pop("contributor_name", "")
        email_raw = cleaned.pop("contributor_email", "")
        id_raw = cleaned.pop("contributor_id", "")

        # Use explicit role if available, otherwise use mapped empty role
        role_value = (
            _standardize_role_names(explicit_contributor_role, role_map)
            if explicit_contributor_role.strip()
            else role_map["contributor_name"]
        )

        # Process this category using modular functions
        category_dict = contributors.parse_contributors(
            name_raw, id_raw, email_raw, role_value
        )

        # Add to combined dict with sequential indices
        for contributor in category_dict.values():
            if contributor["name"]:
                all_contributors[str(current_index)] = contributor
                current_index += 1

    # Deduplicate exact (name, role) pairs. A person legitimately appears once per DISTINCT
    # role (e.g. originator + principalInvestigator), but the SAME person with the SAME role
    # from several source fields — e.g. a curated contributor_name marked principalInvestigator
    # plus a source principal_investigator field — is pure redundancy (mocha showed "Johns,
    # Johns, Johns"). Keep the first occurrence per (normalised name, role), filling in any
    # email/id a later duplicate supplies. Distinct roles for the same person are preserved.
    if all_contributors:
        deduped: dict = {}
        for contributor in all_contributors.values():
            key = (" ".join(contributor["name"].split()).lower(), contributor["role"])
            if key in deduped:
                existing = deduped[key]
                if not existing.get("email") and contributor.get("email"):
                    existing["email"] = contributor["email"]
                if not existing.get("id") and contributor.get("id"):
                    existing["id"] = contributor["id"]
            else:
                deduped[key] = dict(contributor)
        all_contributors = {str(i + 1): c for i, c in enumerate(deduped.values())}

    # Extract any remaining URLs/emails that weren't processed
    remaining_emails = []
    remaining_ids = []

    for key in list(cleaned.keys()):
        if key.endswith("_email"):
            raw = cleaned.pop(key)
            if raw and str(raw).strip():
                parts = [
                    v.strip()
                    for v in str(raw).replace(";", ",").split(",")
                    if v.strip()
                ]
                remaining_emails.extend(parts)

    for key in list(cleaned.keys()):
        if key in ("contributor_url", "creator_url", "publisher_url"):
            raw = cleaned.pop(key)
            if raw and str(raw).strip():
                parts = [
                    v.strip()
                    for v in str(raw).replace(";", ",").split(",")
                    if v.strip()
                ]
                remaining_ids.extend(parts)

    # Convert back to the arrays format for the existing modular processing
    if all_contributors:
        raw_names = [c["name"] for c in all_contributors.values()]
        raw_roles = [c["role"] for c in all_contributors.values()]
        raw_emails = [c["email"] for c in all_contributors.values()]
        raw_ids = [c["id"] for c in all_contributors.values()]

        # Add any remaining emails/IDs that didn't get associated
        while len(raw_emails) < len(raw_names):
            raw_emails.append("")
        while len(raw_ids) < len(raw_names):
            raw_ids.append("")

        # Note: remaining_emails and remaining_ids are deliberately not extended here
        # to avoid misalignment. All emails/IDs should be properly associated during
        # the three-phase processing above.
    else:
        raw_names = []
        raw_roles = []
        raw_emails = remaining_emails
        raw_ids = remaining_ids

    # Pad lists to same length for processing
    max_contributors = max(
        len(raw_names), len(raw_roles), len(raw_emails), len(raw_ids)
    )

    # Only proceed if we have any contributor information
    if max_contributors > 0:
        # Pad shorter lists with empty strings
        while len(raw_names) < max_contributors:
            raw_names.append("")
        while len(raw_roles) < max_contributors:
            raw_roles.append("")
        while len(raw_emails) < max_contributors:
            raw_emails.append("")
        while len(raw_ids) < max_contributors:
            raw_ids.append("")

        # Convert to comma-separated strings for processing
        names_str = ", ".join(raw_names)
        roles_str = ", ".join(raw_roles)
        emails_str = ", ".join(raw_emails)
        ids_str = ", ".join(raw_ids)

        log_debug(
            "Raw contributor data - Names: %r, Roles: %r, Emails: %r, IDs: %r",
            names_str,
            roles_str,
            emails_str,
            ids_str,
        )

        # Use the new modular contributor processing
        try:
            processed = contributors.process_contributor_metadata(
                names_str, ids_str, emails_str, roles_str
            )

            # Update cleaned dictionary with processed results
            cleaned.update(processed)

            # Normalise ids to full URLs (bare ORCID -> https://orcid.org/…; bare web
            # address -> https://…), then backfill email by ORCID now that ids are resolved
            # (registry enrichment runs inside process_contributor_metadata). The same person
            # can appear under several roles with the email on only one row; propagate it.
            _normalize_contributor_ids(cleaned)
            _backfill_contributor_email_by_id(cleaned)

            # Add NERC G04 vocabulary URL if we have contributor roles
            if "contributor_role" in cleaned and cleaned["contributor_role"]:
                cleaned["contributor_role_vocabulary"] = (
                    "https://vocab.nerc.ac.uk/collection/G04/current/"
                )

            log_debug("Processed contributor metadata: %s", processed)

        except (ValueError, KeyError, TypeError, AttributeError) as e:
            log_debug(f"Error in contributor processing: {e}, using fallback")
            # Fallback to basic concatenation if modular processing fails
            cleaned["contributor_name"] = names_str
            cleaned["contributor_role"] = roles_str
            cleaned["contributor_email"] = emails_str
            cleaned["contributor_id"] = ids_str

            # Add vocabulary URL in fallback case too
            if roles_str:
                cleaned["contributor_role_vocabulary"] = (
                    "https://vocab.nerc.ac.uk/collection/G04/current/"
                )

    # Step B: consolidate institution keys using new modular approach
    # Collect all institution-related fields from various sources
    raw_institutions = []
    raw_vocabularies = []
    raw_roles = []

    # Extract institution names from various fields
    for attr_key in list(cleaned.keys()):
        if attr_key.lower() in (
            "institution",
            "publisher_institution",
            "contributor_institution",
            "contributing_institutions",
        ):
            raw_inst = cleaned.pop(attr_key)
            if raw_inst and str(raw_inst).strip():
                raw_institutions.append(str(raw_inst).strip())

    # Extract vocabulary URLs from vocabulary fields
    for attr_key in list(cleaned.keys()):
        if attr_key.lower() in (
            "contributing_institutions_vocabulary",
            "institution_vocabulary",
            "publisher_institution_vocabulary",
        ):
            raw_vocab = cleaned.pop(attr_key)
            if raw_vocab and str(raw_vocab).strip():
                raw_vocabularies.append(str(raw_vocab).strip())

    # Extract roles from role fields
    for attr_key in list(cleaned.keys()):
        if attr_key.lower() in (
            "contributing_institutions_role",
            "institution_role",
            "publisher_institution_role",
        ):
            raw_role = cleaned.pop(attr_key)
            if raw_role and str(raw_role).strip():
                raw_roles.append(str(raw_role).strip())

    # Convert to comma-separated strings for modular processing
    institutions_str = ", ".join(raw_institutions) if raw_institutions else ""
    vocabularies_str = ", ".join(raw_vocabularies) if raw_vocabularies else ""
    roles_str = ", ".join(raw_roles) if raw_roles else ""

    log_debug(
        "Raw institution data - Institutions: %r, Vocabularies: %r, Roles: %r",
        institutions_str,
        vocabularies_str,
        roles_str,
    )

    # Use the new modular institution processing (includes corrections and registry lookup)
    try:
        processed = contributors.process_institution_metadata(
            institutions_str, vocabularies_str, roles_str
        )
        # Update cleaned dictionary with processed results
        cleaned.update(processed)
        _dedup_institution_metadata(cleaned)
        log_debug("Processed institution metadata: %s", processed)

    except (ValueError, KeyError, TypeError, AttributeError) as e:
        log_debug(f"Error in institution processing: {e}, using fallback")
        # Fallback to basic values if modular processing fails
        cleaned["contributing_institutions"] = institutions_str
        cleaned["contributing_institutions_vocabulary"] = vocabularies_str
        cleaned["contributing_institutions_role"] = roles_str

    log_debug("Finished _consolidate_contributors: %s", cleaned)
    return cleaned


def merge_metadata_aliases(attrs: dict, preferred_keys: dict) -> dict:
    """Consolidate and rename metadata keys case‑insensitively (except featureType),
    using preferred_keys to map aliases to canonical names.

    Parameters
    ----------
    attrs : dict
        Metadata dictionary with potential duplicates.
    preferred_keys : dict
        Mapping of lowercase alias keys to preferred canonical keys.

    Returns
    -------
    dict
        Metadata dictionary with duplicates merged and keys renamed.

    """
    merged = {}
    for orig_key, value in attrs.items():
        # Preserve 'featureType' exactly
        if orig_key == "featureType":
            canonical = "featureType"
        elif orig_key == "Conventions":
            canonical = "Conventions"
        else:
            low = orig_key.lower()
            # Rename via the lowercase-alias mapping when present, else keep the lowercased key.
            canonical = preferred_keys.get(low, low)

        # Log any renaming
        if canonical != orig_key:
            log_debug("Renaming key '%s' → '%s'", orig_key, canonical)

        # Merge duplicates by keeping the first or identical values
        if canonical in merged:
            if merged[canonical] == value:
                log_debug(
                    "Skipped duplicate (identical) key '%s' → '%s'", orig_key, canonical
                )
            else:
                log_debug(
                    "Conflict for '%s' from '%s'; keeping first value",
                    canonical,
                    orig_key,
                )
            continue

        merged[canonical] = value

    return merged


_TIME_UNIT_ALIASES = {
    "seconds": "s",
    "second": "s",
    "secs": "s",
    "sec": "s",
    "s": "s",
    "minutes": "m",
    "minute": "m",
    "mins": "m",
    "min": "m",
    "hours": "h",
    "hour": "h",
    "hrs": "h",
    "hr": "h",
    "h": "h",
    "days": "D",
    "day": "D",
    "d": "D",
}


def _parse_cf_time_units(units: str) -> "tuple[str, str] | None":
    """Parse a CF time-units string into a (pandas unit, origin) pair.

    For example ``"days since 1950-01-01"`` returns ``("D", "1950-01-01")``. Returns
    ``None`` if the string is not a recognised ``"<interval> since <date>"`` form, so the
    caller can fall back explicitly rather than silently assuming an epoch.
    """
    match = re.match(r"\s*(\w+)\s+since\s+(.+?)\s*$", units, re.IGNORECASE)
    if not match:
        return None
    pandas_unit = _TIME_UNIT_ALIASES.get(match.group(1).lower())
    if pandas_unit is None:
        return None
    origin = match.group(2).strip()
    # Drop a trailing UTC "Z": pandas' to_datetime(origin=..., unit=...) rejects a
    # timezone-aware origin, and the numeric values are UTC regardless. Without this a
    # units string like "seconds since 1970-01-01T00:00:00Z" fails to decode, leaving the
    # coordinate as raw floats (e.g. calafat2025) instead of datetime64.
    if origin.endswith(("Z", "z")):
        origin = origin[:-1].strip()
    return pandas_unit, origin


def standardize_time_coordinate(ds: xr.Dataset) -> xr.Dataset:
    """Standardize TIME coordinate to comply with AMOCatlas specifications.

    All datasets with a TIME coordinate should have standardized attributes:
    - data type: datetime64[ns]
    - long_name: "Time elapsed since 1970-01-01T00:00:00Z"
    - standard_name: "time"
    - calendar: "gregorian"
    - units: "seconds since 1970-01-01T00:00:00Z"
    - vocabulary: "http://vocab.nerc.ac.uk/collection/OG1/current/TIME/"

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize TIME coordinate for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized TIME coordinate attributes.

    """
    if "TIME" not in ds.coords and "TIME" not in ds.dims:
        return ds

    # Ensure TIME is a coordinate
    if "TIME" in ds.dims and "TIME" not in ds.coords:
        # If TIME is only a dimension, create a coordinate
        log_debug("TIME dimension found without coordinate - creating coordinate")
        if "TIME" in ds.data_vars:
            # If there's a TIME data variable, promote it to coordinate
            ds = ds.set_coords("TIME")
        else:
            # Create a simple index coordinate
            ds = ds.assign_coords(TIME=range(ds.sizes["TIME"]))

    time_coord = ds["TIME"]

    # Convert to datetime64[ns] if not already
    if time_coord.dtype.kind != "M":  # Not datetime64 type
        log_debug(
            f"Converting TIME coordinate from {time_coord.dtype} to datetime64[ns]"
        )

        if time_coord.dtype.kind in ["f", "i"]:  # numeric type (seconds since epoch)
            # Convert numeric time to datetime64[ns]
            import pandas as pd

            try:
                # Handle different epoch references - assume 1970-01-01 if no units specified
                units = time_coord.attrs.get(
                    "units", "seconds since 1970-01-01T00:00:00Z"
                )
                parsed_units = _parse_cf_time_units(units)
                if parsed_units is not None:
                    # Honour the declared interval and epoch, e.g. "days since 1950-01-01".
                    pandas_unit, origin = parsed_units
                    time_datetime = pd.to_datetime(
                        time_coord.values,
                        unit=pandas_unit,
                        origin=origin,
                        errors="coerce",
                    )
                else:
                    # Units not understood: fall back to seconds since 1970-01-01, and warn,
                    # since that assumption is wrong for any other epoch.
                    warnings.warn(
                        f"TIME units {units!r} not understood; assuming "
                        "'seconds since 1970-01-01'.",
                        stacklevel=2,
                    )
                    time_datetime = pd.to_datetime(
                        time_coord.values,
                        unit="s",
                        origin="1970-01-01",
                        errors="coerce",
                    )

                ds["TIME"] = ("TIME", time_datetime.astype("datetime64[ns]"))
            except (
                ValueError,
                TypeError,
                OverflowError,
                pd.errors.OutOfBoundsDatetime,
            ) as e:
                log_debug(f"Failed to convert numeric TIME to datetime64[ns]: {e}")
                # Keep original values but warn
                ds["TIME"] = time_coord
        else:
            log_debug(f"Unknown TIME coordinate dtype: {time_coord.dtype}")
            # Keep original values
            ds["TIME"] = time_coord
    elif time_coord.dtype != "datetime64[ns]":
        # Convert datetime64 to nanosecond precision
        log_debug("Converting datetime64 TIME coordinate to nanosecond precision")
        import pandas as pd

        time_datetime = pd.to_datetime(time_coord.values, errors="coerce").astype(
            "datetime64[ns]"
        )
        ds["TIME"] = ("TIME", time_datetime)

    # Set standard TIME coordinate attributes for datetime64 format
    standard_time_attrs = {
        "long_name": "Time",
        "standard_name": "time",
        "calendar": "gregorian",
        # A valid UDUNITS/CF string, not the numpy dtype name. On write, writers.py moves
        # this to the encoding and pins "seconds since 1970-01-01" for every array, so the
        # saved on-disk units are consistent regardless of each source file's own encoding.
        "units": "seconds since 1970-01-01T00:00:00Z",
        "vocabulary": "http://vocab.nerc.ac.uk/collection/P01/current/ELTMEP01/",
    }

    # Update TIME coordinate attributes
    ds["TIME"].attrs.update(standard_time_attrs)
    log_debug("Standardized TIME coordinate attributes")

    return ds


def standardize_longitude_coordinate(ds: xr.Dataset) -> xr.Dataset:
    """Standardize LONGITUDE coordinate to comply with AMOCatlas specifications.

    All datasets with a LONGITUDE coordinate should have standardized attributes:
    - data type: double
    - long_name: "longitude east (WGS84)"
    - standard_name: "longitude"
    - units: "degree_east"

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize LONGITUDE coordinate for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized LONGITUDE coordinate attributes.

    """
    if "LONGITUDE" not in ds.coords and "LONGITUDE" not in ds.dims:
        return ds

    # Ensure LONGITUDE is a coordinate
    if "LONGITUDE" in ds.dims and "LONGITUDE" not in ds.coords:
        log_debug("LONGITUDE dimension found without coordinate - creating coordinate")
        if "LONGITUDE" in ds.data_vars:
            ds = ds.set_coords("LONGITUDE")
        else:
            ds = ds.assign_coords(LONGITUDE=range(ds.sizes["LONGITUDE"]))

    # Convert to double precision if not already
    if ds["LONGITUDE"].dtype != "float64":
        log_debug(
            f"Converting LONGITUDE coordinate from {ds['LONGITUDE'].dtype} to float64"
        )
        ds["LONGITUDE"] = ds["LONGITUDE"].astype("float64")

    # Set standard LONGITUDE coordinate attributes
    standard_lon_attrs = {
        "long_name": "Longitude",
        "description": "Longitude east (WGS84)",
        "standard_name": "longitude",
        "units": defaults.PREFERRED_UNITS["longitude"],
    }

    ds["LONGITUDE"].attrs.update(standard_lon_attrs)
    log_debug("Standardized LONGITUDE coordinate attributes")

    return ds


def standardize_latitude_coordinate(ds: xr.Dataset) -> xr.Dataset:
    """Standardize LATITUDE coordinate to comply with AMOCatlas specifications.

    All datasets with a LATITUDE coordinate should have standardized attributes:
    - data type: double
    - long_name: "Latitude north (WGS84)"
    - standard_name: "latitude"
    - units: "degree_north"

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize LATITUDE coordinate for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized LATITUDE coordinate attributes.

    """
    if "LATITUDE" not in ds.coords and "LATITUDE" not in ds.dims:
        return ds

    # Ensure LATITUDE is a coordinate
    if "LATITUDE" in ds.dims and "LATITUDE" not in ds.coords:
        log_debug("LATITUDE dimension found without coordinate - creating coordinate")
        if "LATITUDE" in ds.data_vars:
            ds = ds.set_coords("LATITUDE")
        else:
            ds = ds.assign_coords(LATITUDE=range(ds.sizes["LATITUDE"]))

    # Convert to double precision if not already
    if ds["LATITUDE"].dtype != "float64":
        log_debug(
            f"Converting LATITUDE coordinate from {ds['LATITUDE'].dtype} to float64"
        )
        ds["LATITUDE"] = ds["LATITUDE"].astype("float64")

    # Set standard LATITUDE coordinate attributes
    standard_lat_attrs = {
        "long_name": "Latitude",
        "description": "Latitude north (WGS84)",
        "standard_name": "latitude",
        "units": defaults.PREFERRED_UNITS["latitude"],
    }

    ds["LATITUDE"].attrs.update(standard_lat_attrs)
    log_debug("Standardized LATITUDE coordinate attributes")

    return ds


def standardize_depth_coordinate(ds: xr.Dataset) -> xr.Dataset:
    """Standardize DEPTH coordinate to comply with AMOCatlas specifications.

    All datasets with a DEPTH coordinate should have standardized attributes:
    - data type: double
    - long_name: "Depth below surface of the water"
    - standard_name: "depth"
    - units: "meters"

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize DEPTH coordinate for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized DEPTH coordinate attributes.

    """
    if "DEPTH" not in ds.coords and "DEPTH" not in ds.dims:
        return ds

    # Ensure DEPTH is a coordinate
    if "DEPTH" in ds.dims and "DEPTH" not in ds.coords:
        log_debug("DEPTH dimension found without coordinate - creating coordinate")
        if "DEPTH" in ds.data_vars:
            ds = ds.set_coords("DEPTH")
        else:
            ds = ds.assign_coords(DEPTH=range(ds.sizes["DEPTH"]))

    # Convert to double precision if not already
    if ds["DEPTH"].dtype != "float64":
        log_debug(f"Converting DEPTH coordinate from {ds['DEPTH'].dtype} to float64")
        ds["DEPTH"] = ds["DEPTH"].astype("float64")

    # Set standard DEPTH coordinate attributes
    standard_depth_attrs = {
        "long_name": "Depth",
        "description": " Depth below surface of the water",
        "standard_name": "depth",
        "units": defaults.PREFERRED_UNITS["length"],
    }

    ds["DEPTH"].attrs.update(standard_depth_attrs)
    log_debug("Standardized DEPTH coordinate attributes")

    return ds


def standardize_sigma0_coordinate(ds: xr.Dataset) -> xr.Dataset:
    """Standardize SIGMA0 coordinate to comply with AMOCatlas specifications.

    All datasets with a SIGMA0 coordinate should have standardized attributes:
    - data type: double
    - long_name: "Potential density anomaly to 1000 kg/m3, surface reference"
    - standard_name: "sea_water_sigma_theta"
    - units: "kg m-3"

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize SIGMA0 coordinate for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized SIGMA0 coordinate attributes.

    """
    if "SIGMA0" not in ds.coords and "SIGMA0" not in ds.dims:
        return ds

    # Ensure SIGMA0 is a coordinate
    if "SIGMA0" in ds.dims and "SIGMA0" not in ds.coords:
        log_debug("SIGMA0 dimension found without coordinate - creating coordinate")
        if "SIGMA0" in ds.data_vars:
            ds = ds.set_coords("SIGMA0")
        else:
            ds = ds.assign_coords(SIGMA0=range(ds.sizes["SIGMA0"]))

    # Convert to double precision if not already
    if ds["SIGMA0"].dtype != "float64":
        log_debug(f"Converting SIGMA0 coordinate from {ds['SIGMA0'].dtype} to float64")
        ds["SIGMA0"] = ds["SIGMA0"].astype("float64")

    # Set standard SIGMA0 coordinate attributes
    standard_sigma0_attrs = {
        "long_name": "Sigma0",
        "description": "Potential density anomaly to 1000 kg/m3, surface reference",
        "standard_name": "sea_water_sigma_theta",
        "units": defaults.PREFERRED_UNITS["density"],
    }

    ds["SIGMA0"].attrs.update(standard_sigma0_attrs)
    log_debug("Standardized SIGMA0 coordinate attributes")

    return ds


def standardize_units(ds: xr.Dataset) -> xr.Dataset:
    """Standardize variable units throughout the dataset.

    Uses the unit mapping from utilities module.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to standardize units for.

    Returns
    -------
    xr.Dataset
        Dataset with standardized variable units.

    """
    from .utilities import standardize_dataset_units

    return standardize_dataset_units(ds, log_changes=True)


def standardise_samba(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise SAMBA array dataset to consistent format.

    .. deprecated::
        This function is deprecated. Use :func:`standardise_data` instead.

    Parameters
    ----------
    ds : xr.Dataset
        Raw SAMBA dataset to standardise.
    file_name : str
        Original filename for metadata.

    Returns
    -------
    xr.Dataset
        Standardised dataset with consistent metadata and formatting.

    """
    warnings.warn(
        "standardise_samba() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_data(ds, file_name)


def standardise_rapid(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise RAPID array dataset to consistent format.

    .. deprecated::
        This function is deprecated. Use :func:`standardise_data` instead.

    Parameters
    ----------
    ds : xr.Dataset
        Raw RAPID dataset to standardise.
    file_name : str
        Original filename for metadata.

    Returns
    -------
    xr.Dataset
        Standardised dataset with consistent metadata and formatting.

    """
    warnings.warn(
        "standardise_rapid() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_data(ds, file_name)


def standardise_move(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise MOVE array dataset to consistent format.

    Parameters
    ----------
    ds : xr.Dataset
        Raw MOVE dataset to standardise.
    file_name : str
        Original filename for metadata.

    Returns
    -------
    xr.Dataset
        Standardised dataset with consistent metadata and formatting.

    """
    warnings.warn(
        "standardise_move() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_osnap(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise OSNAP array dataset to consistent format."""
    warnings.warn(
        "standardise_osnap() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_fw2015(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise FW2015 array dataset to consistent format."""
    warnings.warn(
        "standardise_move() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_mocha(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise MOCHA array dataset to consistent format."""
    warnings.warn(
        "standardise_mocha() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_41n(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise 41N array dataset to consistent format."""
    warnings.warn(
        "standardise_41n() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_dso(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise DSO array dataset to consistent format."""
    warnings.warn(
        "standardise_dso() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_calafat2025(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise CALAFAT2025 array dataset to consistent format."""
    warnings.warn(
        "standardise_calafat2025() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_zheng2024(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise ZHENG2024 array dataset to consistent format."""
    warnings.warn(
        "standardise_zheng2024() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_47n(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise 47N array dataset to a consistent format.

    Parameters
    ----------
    ds : xr.Dataset
        Raw 47N array dataset to standardise.
    file_name : str
        Original filename associated with the dataset, used for metadata.

    Returns
    -------
    xr.Dataset
        Standardised dataset with consistent metadata and formatting for the 47N array.

    """
    warnings.warn(
        "standardise_47n() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_fbc(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise FBC array dataset to consistent format."""
    warnings.warn(
        "standardise_fbc() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_array(ds, file_name)


def standardise_arcticgateway(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise Arctic Gateway array dataset to consistent format."""
    warnings.warn(
        "standardise_arcticgateway() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_nac(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise NAC array dataset to consistent format."""
    warnings.warn(
        "standardise_nac() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_sf2021(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise SF2021 array dataset to consistent format."""
    warnings.warn(
        "standardise_sf2021() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_lebras35n(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise LEBRAS35N array dataset to consistent format."""
    warnings.warn(
        "standardise_lebras35n() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_axmoc22s(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise AXMOC22S array dataset to consistent format."""
    warnings.warn(
        "standardise_axmoc22s() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_axmoc34s(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise AXMOC34S array dataset to consistent format."""
    warnings.warn(
        "standardise_axmoc34s() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return standardise_array(ds, file_name)


def standardise_data(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise a dataset using YAML-based metadata.

    Parameters
    ----------
    ds : xr.Dataset
        Raw dataset loaded from a reader with amocatlas_datasource metadata.
    file_name : str
        Filename (e.g., 'moc_transports.nc') expected to match ds.attrs["source_file"].

    Returns
    -------
    xr.Dataset
        Standardised dataset with renamed variables and enriched metadata.

    Raises
    ------
    ValueError
        If file_name does not match ds.attrs["source_file"].
    ValueError
        If amocatlas_datasource is not found in dataset metadata.

    """
    # 1) Validate source_file matches
    src = ds.attrs.get("source_file")
    if src and src != file_name:
        raise ValueError(f"file_name {file_name!r} ≠ ds.attrs['source_file'] {src!r}")

    # 2) Get datasource ID from dataset metadata
    datasource_id = ds.attrs.get("processing_datasource")
    if not datasource_id:
        raise ValueError("Dataset missing required 'processing_datasource' metadata")

    log_debug(f"Standardising {file_name} for {datasource_id.upper()}")

    # 3) Collect new attrs from YAML
    meta = utilities.load_array_metadata(datasource_id)
    file_meta = meta["files"].get(file_name, {})

    # 3.5) Remove unwanted variables if specified
    variables_to_remove = file_meta.get("variables_to_remove", [])
    if variables_to_remove:
        # Handle case where YAML parser returns a string instead of list
        if isinstance(variables_to_remove, str):
            variables_to_remove = variables_to_remove.split()
            log_debug(f"Converted string to list: {variables_to_remove}")

        vars_removed = []
        for var_name in variables_to_remove:
            if var_name in ds.variables:
                ds = ds.drop_vars(var_name)
                vars_removed.append(var_name)
                log_debug(f"Removed variable '{var_name}' from dataset")
            else:
                log_debug(f"Variable '{var_name}' not found for removal")

        if vars_removed:
            log_debug(f"Removed {len(vars_removed)} variables: {vars_removed}")

    # Apply per-variable metadata BEFORE renaming (metadata refers to original variable names)
    var_meta = file_meta.get("original_variable_metadata", {})
    for var_name, attrs in var_meta.items():
        if var_name in ds.variables:
            ds[var_name].attrs.update(attrs)
            log_debug(f"Applied metadata to original variable '{var_name}'")

    # Rename variables and track what was actually renamed
    # Prefer dataset's variable_mapping (which may have sanitized names) over YAML
    rename_dict = ds.attrs.get(
        "variable_mapping", file_meta.get("variable_mapping", {})
    )
    applied_mapping = {}

    if rename_dict:
        # Only rename variables that actually exist and need renaming
        valid_renames = {
            old: new
            for old, new in rename_dict.items()
            if old in ds.variables and old != new
        }

        if valid_renames:
            ds = ds.rename(valid_renames)
            applied_mapping.update(valid_renames)
            log_debug("Applied variable renaming: %s", valid_renames)

        # For variables that couldn't be renamed (case mismatch, etc.),
        # try to find them with case-insensitive matching and track pass-through
        failed_renames = {
            old: new
            for old, new in rename_dict.items()
            if old not in ds.variables and old != new
        }

        if failed_renames:
            log_debug("Failed to find exact matches for renaming: %s", failed_renames)

            # Try case-insensitive matching for pass-through tracking
            ds_vars_lower = {var.lower(): var for var in ds.variables}
            for orig_name, std_name in failed_renames.items():
                orig_lower = orig_name.lower()
                if orig_lower in ds_vars_lower:
                    actual_var = ds_vars_lower[orig_lower]
                    # Track as pass-through: actual_name -> actual_name (no rename occurred)
                    applied_mapping[actual_var] = actual_var
                    log_debug(
                        "Pass-through (case mismatch): %s (expected %s -> %s)",
                        actual_var,
                        orig_name,
                        std_name,
                    )

        # Track coordinates that were successfully renamed
        coord_renames = {
            old: new
            for old, new in rename_dict.items()
            if old in ds.coords and old != new
        }
        if coord_renames:
            applied_mapping.update(coord_renames)

    # Always track applied mapping (even if empty) for consistent reporting
    if applied_mapping:
        ds.attrs["applied_variable_mapping"] = applied_mapping
        log_debug(
            "Total applied mapping (renames + pass-throughs): %s", applied_mapping
        )
    else:
        log_debug("No variable_mapping found or applied for %s", file_name)

    # Handle convert_to_coord directive
    convert_to_coord = file_meta.get("convert_to_coord")
    if convert_to_coord:
        # Check if this variable was renamed - look for the mapped name
        target_var = convert_to_coord
        if rename_dict and convert_to_coord in rename_dict:
            target_var = rename_dict[convert_to_coord]
            log_debug(
                f"Using mapped variable name '{target_var}' for convert_to_coord (was '{convert_to_coord}')"
            )

        if target_var in ds.data_vars:
            log_debug(f"Converting variable '{target_var}' to coordinate")
            # Get the variable data and attributes
            var_data = ds[target_var]
            var_attrs = var_data.attrs.copy()

            # Remove the variable from data_vars and add as coordinate
            ds = ds.drop_vars(target_var)
            ds = ds.assign_coords({target_var: var_data})

            # Restore attributes
            ds[target_var].attrs.update(var_attrs)
            log_debug(f"Successfully converted '{target_var}' to coordinate")
        else:
            log_debug(
                f"Variable '{target_var}' not found in dataset for coordinate conversion"
            )

    # Variable metadata was already applied before renaming (lines 1125-1130)

    # Special handling for heat transport unit conversion (W to PW)
    # Convert any remapped variable with units="W" and standard_name containing "northward_ocean_heat_transport"
    for var_name in ds.variables:
        var_attrs = ds[var_name].attrs
        if var_attrs.get(
            "units"
        ) == "W" and "northward_ocean_heat_transport" in var_attrs.get(
            "standard_name", ""
        ):
            log_debug(f"Converting heat transport variable '{var_name}' from W to PW")
            # Preserve all attributes before conversion
            original_attrs = ds[var_name].attrs.copy()
            # Convert data from watts to petawatts (divide by 10^15)
            ds[var_name] = ds[var_name] / 1e15
            # Restore all attributes and update units
            ds[var_name].attrs = original_attrs
            ds[var_name].attrs["units"] = "PW"

    # If any attributes are blank or value 'n/a', remove them
    for var_name, attrs in list(var_meta.items()):
        if var_name in ds.variables:
            for attr_key, attr_value in attrs.items():
                if attr_value in ("", "n/a"):
                    ds[var_name].attrs.pop(attr_key, None)
                    log_debug(
                        "Removed blank attribute '%s' from variable '%s'",
                        attr_key,
                        var_name,
                    )
    # Remove any empty attributes from the dataset
    for attr_key, attr_value in list(
        ds.attrs.items()
    ):  # Iterate over a copy of the items
        if attr_value in ("", "n/a"):
            ds.attrs.pop(attr_key, None)
            log_debug("Removed blank attribute '%s' from dataset", attr_key)

    # 3) Merge existing attrs + new global attrs + file-specific with conflict tracking
    combined = {}

    # Start with original file metadata (highest priority base)
    for key, value in ds.attrs.items():
        combined[key] = value

    # Add array-level YAML metadata with conflict resolution
    array_metadata = meta.get("metadata", {})
    # Nominal time_coverage is skipped from the merge below (it is derived from the TIME
    # coordinate); keep the declared values as a fallback for datasets where the TIME
    # coordinate cannot be used, so a declared coverage is never silently dropped.
    _nominal_tc = {
        key: array_metadata[key]
        for key in _TIME_COVERAGE_KEYS
        if array_metadata.get(key) not in (None, "")
    }
    for key, value in array_metadata.items():
        if key in _TIME_COVERAGE_KEYS:
            # Derived from the TIME coordinate below; ignore the nominal YAML value
            # (which is often wrong by days) instead of raising a conflict.
            continue
        if key in combined:
            resolved_value = resolve_metadata_conflict(
                key, combined[key], value, "original file", "array-level YAML"
            )
            combined[key] = resolved_value
        else:
            combined[key] = value

    # Add special mappings
    special_mappings = {
        "summary": meta["metadata"].get("description", ""),
        "weblink": meta["metadata"].get("weblink", ""),
    }
    for key, value in special_mappings.items():
        if value and key in combined:
            resolved_value = resolve_metadata_conflict(
                key, combined[key], value, "existing", "array-level YAML mapping"
            )
            combined[key] = resolved_value
        elif value:
            combined[key] = value

    # Add file-specific metadata with conflict resolution
    file_specific_fields = ("acknowledgment", "data_product", "citation")
    for key in file_specific_fields:
        if key in file_meta:
            if key in combined:
                resolved_value = resolve_metadata_conflict(
                    key, combined[key], file_meta[key], "existing", "file-specific YAML"
                )
                combined[key] = resolved_value
            else:
                combined[key] = file_meta[key]

    # 4) Apply field renaming first, then overwrites, then contributor processing
    # This ensures overwrites can target renamed fields while preventing institutional contamination

    # 4.1) First do field renaming (normalize whitespace and merge aliases)
    combined = utilities.normalize_whitespace(combined)
    merged_attrs = merge_metadata_aliases(combined, defaults.METADATA_KEY_MAPPINGS)

    # 4.2) Then apply overwrite directives to renamed fields
    all_yaml_metadata = {}
    all_yaml_metadata.update(meta.get("metadata", {}))  # array-level
    all_yaml_metadata.update(file_meta)  # file-level

    overwrite_applied = {}
    overwrite_keys_to_remove = []
    for key, value in all_yaml_metadata.items():
        if key.endswith("_overwrite"):
            # Extract the base key name (remove _overwrite suffix)
            base_key = key[:-10]  # Remove "_overwrite" (10 characters)

            # Force overwrite the attribute even if it already exists
            merged_attrs[base_key] = value
            overwrite_applied[base_key] = value
            overwrite_keys_to_remove.append(key)  # Mark for cleanup
            log_debug(
                f"Applied overwrite: '{base_key}' = '{str(value)[:50]}{'...' if len(str(value)) > 50 else ''}'"
            )

    if overwrite_applied:
        log_debug(
            f"Applied {len(overwrite_applied)} metadata overrides: {list(overwrite_applied.keys())}"
        )

    # 4.3) Now do contributor consolidation on the renamed and overwritten fields
    cleaned = _consolidate_contributors(merged_attrs)

    # Remove _overwrite fields from cleaned metadata to prevent them from appearing in final dataset
    for key in overwrite_keys_to_remove:
        cleaned.pop(key, None)
        log_debug(f"Removed processing directive: '{key}'")

    # 4.4) Process remove_unwanted_attributes directive
    remove_unwanted = all_yaml_metadata.get("remove_unwanted_attributes", [])
    if remove_unwanted:
        for attr_name in remove_unwanted:
            if attr_name in cleaned:
                cleaned.pop(attr_name)
                log_debug(f"Removed unwanted attribute: '{attr_name}'")
        # Also remove the remove_unwanted_attributes directive itself
        cleaned.pop("remove_unwanted_attributes", None)

    # 5) Standardize date formats and add processing metadata

    def standardize_date_format(date_string: str) -> str:
        """Standardize date to ISO 8601 format with Z timezone: YYYY-MM-DDTHH:MM:SSZ

        Handles various input formats and converts to UTC with Z suffix.
        """
        if not date_string or date_string.strip() == "":
            return date_string

        date_str = str(date_string).strip()

        # If already in correct format, return as-is
        if date_str.endswith("Z") and "T" in date_str and len(date_str) == 20:
            return date_str

        # Common date formats to try parsing
        formats_to_try = [
            "%Y-%m-%dT%H:%M:%SZ",  # Already correct
            "%Y-%m-%dT%H:%M:%S",  # Missing Z
            "%Y-%m-%d %H:%M:%S",  # Space instead of T
            "%Y-%m-%d",  # Date only
            "%Y-%m-%dT%H:%M:%S.%fZ",  # With microseconds and Z
            "%Y-%m-%dT%H:%M:%S.%f",  # With microseconds, no Z
            "%d-%m-%Y",  # European format
            "%m/%d/%Y",  # US format
            "%Y%m%d",  # Compact format
        ]

        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Return in standard format with Z
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

        # If no format worked, return original
        log_debug(f"Could not parse date format: {date_str}")
        return date_string

    def standardize_license_format(license_string: str) -> str:
        """Standardize license to SPDX identifier format where possible.

        Converts common Creative Commons license variations to standard SPDX identifiers.
        """
        if not license_string or license_string.strip() == "":
            return license_string

        license_str = str(license_string).strip()

        # Creative Commons Attribution 4.0 variations
        cc_by_4_patterns = [
            "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "Creative Commons Attribution 4.0 International",
            "CC BY 4.0",
            "CC-BY 4.0",
            "CCBY4.0",
            "CC BY-4.0",
        ]

        # Check for CC BY 4.0 variations (case insensitive)
        license_lower = license_str.lower()
        if any(pattern.lower() in license_lower for pattern in cc_by_4_patterns):
            if (
                "cc" in license_lower
                and "by" in license_lower
                and "4.0" in license_lower
            ):
                return "CC-BY-4.0"

        # Other common licenses (can be extended)
        license_mappings = {
            "ODC-By": "ODC-BY",  # Open Data Commons Attribution
            "odc-by": "ODC-BY",
            "MIT": "MIT",
            "Apache-2.0": "Apache-2.0",
            "BSD-3-Clause": "BSD-3-Clause",
        }

        # Check exact matches first
        if license_str in license_mappings:
            return license_mappings[license_str]

        # Check case-insensitive matches
        for original, standardized in license_mappings.items():
            if license_str.lower() == original.lower():
                return standardized

        # If no standardization found, return original
        return license_str

    # Standardize date fields in metadata
    date_fields = [
        "date_created",
        "date_modified",
        "date_issued",
        "date_metadata_modified",
    ]
    for field in date_fields:
        if field in cleaned and cleaned[field]:
            cleaned[field] = standardize_date_format(cleaned[field])

    # Standardize license field
    if "license" in cleaned and cleaned["license"]:
        cleaned["license"] = standardize_license_format(cleaned["license"])

    def sanitize_source_path(path_string: str) -> str:
        """Sanitize source paths to remove specific user directory structures.

        Replaces hardcoded paths with generic equivalents for portability.
        Only affects display - other users will see their full paths unchanged.
        """
        if not path_string or path_string.strip() == "":
            return path_string

        path_str = str(path_string).strip()

        # Replace the user's home directory with "~" so published reports never leak an
        # absolute local path (e.g. /Users/<name>/.amocatlas_data/... or a repo checkout).
        # User-agnostic: matches whoever ran the processing.
        home = os.path.expanduser("~")
        if path_str.startswith(home):
            sanitized = "~" + path_str[len(home) :]
            log_debug(f"Sanitized source path: {path_str} → {sanitized}")
            return sanitized

        return path_str

    # Sanitize path fields in metadata
    path_fields = ["source_path", "source_file"]
    for field in path_fields:
        if field in cleaned and cleaned[field]:
            cleaned[field] = sanitize_source_path(cleaned[field])

    # Remove old comment-based processing info if it exists
    if "comment" in cleaned:
        comment = cleaned["comment"]
        if (
            "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas"
            in comment
        ):
            # Remove this text from comment, keeping other parts
            cleaned_comment = comment.replace(
                "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
                "",
            ).strip()
            if cleaned_comment:
                cleaned["comment"] = cleaned_comment
            else:
                cleaned.pop("comment", None)

    # Add proper processing metadata
    cleaned["processing_software"] = "http://github.com/AMOCcommunity/amocatlas"
    cleaned["processing_version"] = get_dynamic_version()
    cleaned["date_modified"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Remove internal metadata fields from final dataset
    cleaned.pop("amocatlas_datasource", None)

    # Ensure Conventions includes OceanSITES-1.5
    if "Conventions" in cleaned:
        conventions = cleaned["Conventions"]
        if "OceanSITES-1.5" not in conventions:
            # Append OceanSITES-1.5 to existing conventions
            cleaned["Conventions"] = f"{conventions}, OceanSITES-1.5"
    else:
        # Set default conventions if none exist
        cleaned["Conventions"] = "CF-1.8, ACDD-1.3, OceanSITES-1.5"

    # 6) Normalize and add vocabularies
    normalizations = defaults.PLATFORM_NORMALIZATIONS
    cleaned = normalize_and_add_vocabulary(cleaned, normalizations)

    # 7) Standardize coordinate attributes
    ds = standardize_time_coordinate(ds)
    ds = standardize_longitude_coordinate(ds)
    ds = standardize_latitude_coordinate(ds)
    ds = standardize_depth_coordinate(ds)
    ds = standardize_sigma0_coordinate(ds)

    # 8) Standardize units
    ds = standardize_units(ds)

    # 9) Apply cleaned metadata and reorder according to canonical order.
    # Drop internal working directives that leaked into attrs: these are only used during
    # processing, not in the output. "files"/"variable_mapping"/"original_variable_metadata"
    # are nested dicts (not netCDF-serialisable); "variables_to_remove" is a processing
    # directive already applied above (its variables are gone), so the list itself is stale.
    # (applied_variable_mapping is intentionally kept — it is part of the public attrs.)
    for _internal_attr in (
        "files",
        "variable_mapping",
        "original_variable_metadata",
        "variables_to_remove",
    ):
        cleaned.pop(_internal_attr, None)

    # Insert a missing space after an ISO timestamp in `history`: some upstream files run
    # the timestamp straight into the message (e.g. "...07ZOceanSITES file..."). Only fires
    # when a letter immediately follows the timestamp, so separators like "; " are untouched.
    if cleaned.get("history"):
        cleaned["history"] = re.sub(
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)(?=[A-Za-z])",
            r"\1 ",
            str(cleaned["history"]),
        )

    # time_coverage_start/end are authoritative from the standardized TIME coordinate,
    # not the nominal YAML/file attrs. Computed here so they always match the served data
    # (and flow through to the report, which reads these from the dataset attrs).
    tc_start, tc_end = _time_coverage_from_data(ds)
    if tc_start is not None:
        cleaned["time_coverage_start"] = tc_start
        cleaned["time_coverage_end"] = tc_end
    else:
        # Could not derive from the TIME coordinate (no datetime64 TIME/time variable, or
        # all values NaT). Fall back to the nominal YAML values that were skipped from the
        # merge — without a file value already present, dropping them would regress the
        # coverage the array used to serve. Warn so the substitution is inspectable.
        for key in _TIME_COVERAGE_KEYS:
            if key not in cleaned and key in _nominal_tc:
                cleaned[key] = _nominal_tc[key]
        warnings.warn(
            "time_coverage could not be derived from the TIME coordinate "
            "(no datetime64 TIME/time variable); serving the nominal time_coverage "
            "from the source file or array metadata instead.",
            stacklevel=2,
        )

    ds.attrs = cleaned
    ds.attrs = reorder_metadata(ds.attrs)

    # 10) Apply unit standardization again after metadata processing
    # This ensures units are not overwritten by YAML metadata operations
    ds = standardize_units(ds)

    #    ds = utilities.safe_update_attrs(ds, cleaned, overwrite=False)
    return ds


def standardise_array(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    """Standardise a mooring array dataset using YAML-based metadata.

    .. deprecated::
        This function is deprecated. Use :func:`standardise_data` instead.

    Parameters
    ----------
    ds : xr.Dataset
        Raw dataset loaded from a reader with amocatlas_datasource metadata.
    file_name : str
        Filename (e.g., 'moc_transports.nc') expected to match ds.attrs["source_file"].

    Returns
    -------
    xr.Dataset
        Standardised dataset with renamed variables and enriched metadata.

    """
    warnings.warn(
        "standardise_array() is deprecated and will be removed in a future version. "
        "Use standardise_data() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return standardise_data(ds, file_name)
