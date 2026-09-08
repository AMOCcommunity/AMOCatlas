"""Contributor standardization and consolidation module.

This module provides functions to:
- Parse comma-separated contributor metadata into structured dictionaries
- Enrich contributor data using the ORCID registry
- Format structured contributor data back to comma-separated strings
- Standardize contributor names using the registry
"""

import re
import warnings
from pathlib import Path

import yaml

from amocatlas.defaults import INSTITUTION_CORRECTIONS
from amocatlas.logger import log_debug


def _split_clean(value: str) -> list[str]:
    """Split and clean comma and/or semicolon-separated values.

    Handles mixed delimiters by first splitting on semicolons, then commas.
    Preserves empty strings to maintain positional alignment.

    Args:
        value: String to split (e.g., "A, B; C")

    Returns
    -------
        List of cleaned strings (e.g., ["A", "B", "C"])

    Examples
    --------
        >>> _split_clean("A, B, C")
        ["A", "B", "C"]
        >>> _split_clean("A; B; C")
        ["A", "B", "C"]
        >>> _split_clean("A, B; C")
        ["A", "B", "C"]
        >>> _split_clean("A, , C")
        ["A", "", "C"]

    """
    if not value or not value.strip():
        return []

    # First split by semicolons, then by commas within each part
    parts = []
    for semicolon_part in value.split(";"):
        comma_parts = semicolon_part.split(",")
        for part in comma_parts:
            cleaned = part.strip()
            # Keep all parts (including empty) to preserve positional alignment
            parts.append(cleaned)
    return parts


def _deduplicate_structured_dict(
    entries_dict: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Remove exact duplicate entries from a structured dictionary.

    Parameters
    ----------
    entries_dict : Dict[str, Dict[str, str]]
        Dictionary with string keys ("1", "2", etc.) and values containing
        dictionaries with entry data (e.g., {"name": "...", "role": "...", "email": "...", "id": "..."}).

    Returns
    -------
    Dict[str, Dict[str, str]]
        Dictionary with duplicates removed, maintaining original order with reindexed keys.

    Examples
    --------
    >>> data = {
    ...     "1": {"name": "John Doe", "role": "creator", "email": "john@ex.com", "id": "123"},
    ...     "2": {"name": "John Doe", "role": "creator", "email": "john@ex.com", "id": "123"},
    ...     "3": {"name": "Jane Smith", "role": "PI", "email": "jane@ex.com", "id": "456"}
    ... }
    >>> result = _deduplicate_structured_dict(data)
    >>> len(result)
    2
    >>> result["1"]["name"]
    'John Doe'
    >>> result["2"]["name"]
    'Jane Smith'

    """
    if not entries_dict:
        return entries_dict

    # Process entries in original order (sorted by key as integers)
    seen_tuples = set()
    unique_entries = []

    # Sort keys numerically to maintain original order
    for key in sorted(entries_dict.keys(), key=lambda x: int(x)):
        entry = entries_dict[key]

        # Skip completely empty entries (all fields are empty or whitespace)
        if all(not entry.get(field, "").strip() for field in entry):
            continue

        # Create a tuple of all values in a consistent order
        # Using sorted() to ensure consistent field order
        entry_tuple = tuple(entry.get(field, "") for field in sorted(entry.keys()))

        if entry_tuple not in seen_tuples:
            unique_entries.append(entry)
            seen_tuples.add(entry_tuple)

    # Rebuild dictionary with reindexed keys starting from 1
    result = {}
    for i, entry in enumerate(unique_entries):
        result[str(i + 1)] = entry

    return result


def is_valid_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address string to validate

    Returns
    -------
        True if email appears to be valid, False otherwise

    Examples
    --------
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid.email")
        False
        >>> is_valid_email("")
        False
        >>> is_valid_email("user@domain")
        False

    """
    if not email or not email.strip():
        return False

    # Basic email regex pattern - covers most common cases
    # Allows: letters, numbers, dots, hyphens, underscores, plus signs in local part
    # Requires @ symbol and valid domain with at least one dot
    pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    return bool(re.match(pattern, email.strip()))


def _load_contributor_registry() -> dict | None:
    """Load the contributor registry from YAML file.

    Returns
    -------
        Dict containing the contributor registry, or None if loading fails.

    """
    try:
        registry_file = Path(__file__).parent / "metadata" / "contributor_registry.yml"
        with open(registry_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        log_debug(
            f"Loaded contributor registry with {len(data.get('contributors', {}))} contributors"
        )
    except (FileNotFoundError, OSError, yaml.YAMLError) as e:
        log_debug(f"Could not load contributor registry: {e}")
        return None
    else:
        return data


def _find_contributor_by_name(name: str, registry: dict) -> tuple[str, dict] | None:
    """Find a contributor in the registry by name variants.

    Args:
        name: The name to search for
        registry: The loaded contributor registry

    Returns
    -------
        Tuple of (orcid, contributor_info) if found, None otherwise

    """
    if not registry or not name:
        return None

    contributors = registry.get("contributors", {})
    name_lower = name.lower().strip()

    for orcid, contributor_info in contributors.items():
        # Check standard name
        if contributor_info.get("standard_name", "").lower().strip() == name_lower:
            return orcid, contributor_info

        # Check name variants
        for variant in contributor_info.get("name_variants", []):
            if variant.lower().strip() == name_lower:
                return orcid, contributor_info

    return None


_ORCID_URL_RE = re.compile(r"^https?://(www\.)?orcid\.org/", re.IGNORECASE)


def _is_orcid_url(value: str) -> bool:
    """Return True if a value is an ORCID URL (scheme + host ``orcid.org``).

    Anchored on the host so lookalike strings that merely contain ``orcid.org/``
    as a substring (e.g. ``https://notorcid.org/x`` or a ``?ref=orcid.org/x``
    query) are not mistaken for an ORCID.
    """
    return isinstance(value, str) and bool(_ORCID_URL_RE.match(value))


def _find_contributor_by_orcid(
    orcid_url: str, registry: dict
) -> tuple[str, dict] | None:
    """Find a contributor in the registry by ORCID URL.

    Args:
        orcid_url: The ORCID URL to search for
        registry: The loaded contributor registry

    Returns
    -------
        Tuple of (orcid, contributor_info) if found, None otherwise

    """
    if not registry or not orcid_url:
        return None

    contributors = registry.get("contributors", {})

    # Extract ORCID ID from URL if needed
    orcid_id = orcid_url.strip()
    if "orcid.org/" in orcid_id:
        orcid_id = orcid_id.split("orcid.org/")[-1]

    # Check direct ORCID match
    if orcid_id in contributors:
        return orcid_id, contributors[orcid_id]

    # Check by id_url field
    for orcid, contributor_info in contributors.items():
        if contributor_info.get("id_url", "") == orcid_url:
            return orcid, contributor_info

    return None


def parse_contributors(
    contributor_name: str,
    contributor_id: str,
    contributor_email: str,
    contributor_role: str,
) -> dict[str, dict[str, str]]:
    """Parse comma-separated contributor strings into a structured dictionary.

    Args:
        contributor_name: Comma-separated string of contributor names
        contributor_id: Comma-separated string of contributor IDs/URLs
        contributor_email: Comma-separated string of contributor emails
        contributor_role: Comma-separated string of contributor roles

    Returns
    -------
        Dictionary with string keys "1", "2", etc. and values containing
        dictionaries with keys: name, id, email, role

    Examples
    --------
        >>> parse_contributors("Yao Fu, Penny Holliday", ",", "yao.fu@fsu.edu", "creator, PI")
        {
            "1": {"name": "Yao Fu", "email": "yao.fu@fsu.edu", "id": "", "role": "creator"},
            "2": {"name": "Penny Holliday", "email": "", "id": "", "role": "PI"}
        }

        >>> parse_contributors("A, B; C", "", "", "")
        {
            "1": {"name": "A", "email": "", "id": "", "role": ""},
            "2": {"name": "B", "email": "", "id": "", "role": ""},
            "3": {"name": "C", "email": "", "id": "", "role": ""}
        }

    """
    # Parse all fields using shared helper
    names = _split_clean(contributor_name)
    ids = _split_clean(contributor_id)
    emails = _split_clean(contributor_email)
    roles = _split_clean(contributor_role)

    # Find maximum length to determine number of contributors
    max_len = max(len(names), len(ids), len(emails), len(roles))

    if max_len == 0:
        return {}

    # A single role given for a list of contributors applies to all of them (e.g. one
    # "coAuthor"/"contributor" role for five co-authors), not just the first name.
    if len(roles) == 1 and max_len > 1:
        roles = roles * max_len

    # Build result dictionary
    result = {}
    for i in range(max_len):
        result[str(i + 1)] = {
            "name": names[i] if i < len(names) else "",
            "id": ids[i] if i < len(ids) else "",
            "email": emails[i] if i < len(emails) else "",
            "role": roles[i] if i < len(roles) else "",
        }

    # Heuristic check: commas separate contributors, so a "Last, First" name is
    # silently split into two people. A parsed name that is a single word (no internal
    # whitespace) is the tell-tale sign of such a split — warn so a curator can switch
    # to ";" as the separator. Only flag when there are multiple contributors.
    if max_len >= 2:
        single_word = [
            entry["name"]
            for entry in result.values()
            if entry["name"] and " " not in entry["name"]
        ]
        if single_word:
            warnings.warn(
                f"Contributor name(s) parsed as a single word: {single_word}. "
                "Commas separate contributors, so a 'Last, First' name is split into "
                "two people; use ';' between contributors to disambiguate.",
                stacklevel=2,
            )

    log_debug(f"Parsed {max_len} contributors from metadata")
    return result


def enrich_contributors(
    contributors_dict: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Enrich contributor data using the contributor registry.

    This function:
    1. Loads the contributor registry
    2. For each contributor, tries to find a match by name or existing ID
    3. Updates the contributor with standardized name and ORCID ID if found
    4. Preserves existing data when no registry match is found

    Args:
        contributors_dict: Dictionary from parse_contributors()

    Returns
    -------
        Updated dictionary with enriched contributor information

    Examples
    --------
        >>> contributors = {"1": {"name": "Yao Fu", "email": "yao.fu@fsu.edu", "id": "", "role": "creator"}}
        >>> enrich_contributors(contributors)
        {"1": {"name": "Yao Fu", "email": "yao.fu@fsu.edu", "id": "https://orcid.org/0000-0003-2227-3694", "role": "creator"}}

    """
    registry = _load_contributor_registry()
    if not registry:
        log_debug("No contributor registry available, returning unchanged data")
        return contributors_dict

    result = {}

    for key, contributor in contributors_dict.items():
        updated_contributor = contributor.copy()

        # Validate email if provided
        email = contributor.get("email", "").strip()
        if email and not is_valid_email(email):
            log_debug(
                f"Warning: Invalid email format for contributor '{contributor.get('name', 'Unknown')}': {email}"
            )

        match_info = None

        # Try to find by existing ID first (if provided)
        if contributor.get("id") and contributor["id"].strip():
            match_info = _find_contributor_by_orcid(contributor["id"], registry)
            if match_info:
                log_debug(f"Found registry match by ID: {contributor['id']}")

        # If no ID match and we have a name, try name lookup
        if not match_info and contributor.get("name") and contributor["name"].strip():
            match_info = _find_contributor_by_name(contributor["name"], registry)
            if match_info:
                log_debug(f"Found registry match by name: {contributor['name']}")

        # Update contributor with registry information if found
        if match_info:
            orcid, contributor_info = match_info

            # Update name to standardized form
            standard_name = contributor_info.get(
                "standard_name", contributor.get("name", "")
            )
            updated_contributor["name"] = standard_name

            # Prefer the registry id_url only when it is a real ORCID, so a genuine
            # incoming ORCID is never overwritten by a non-ORCID placeholder (some
            # registry entries hold a personal or lab webpage). Precedence: a registry
            # ORCID standardises the id; otherwise keep an incoming ORCID; otherwise
            # fall back to whatever the registry provides.
            registry_id = contributor_info.get("id_url", "")
            existing_id = (contributor.get("id") or "").strip()
            if _is_orcid_url(registry_id):
                updated_contributor["id"] = registry_id
            elif _is_orcid_url(existing_id):
                updated_contributor["id"] = existing_id
            elif registry_id:
                updated_contributor["id"] = registry_id

            log_debug(
                f"Enriched contributor: '{contributor.get('name', '')}' -> '{standard_name}' ({orcid})"
            )

        result[key] = updated_contributor

    return result


def format_contributors(contributors_dict: dict[str, dict[str, str]]) -> dict[str, str]:
    """Format structured contributor data back to comma-separated strings.

    Args:
        contributors_dict: Dictionary from parse_contributors() or enrich_contributors()

    Returns
    -------
        Dictionary with keys: contributor_name, contributor_id, contributor_email, contributor_role

    Examples
    --------
        >>> contributors = {
        ...     "1": {"name": "Yao Fu", "email": "yao.fu@fsu.edu", "id": "https://orcid.org/0000-0003-2227-3694", "role": "creator"},
        ...     "2": {"name": "N. Penny Holliday", "email": "", "id": "https://orcid.org/0000-0002-9733-8002", "role": "PI"}
        ... }
        >>> format_contributors(contributors)
        {
            "contributor_name": "Yao Fu, N. Penny Holliday",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, https://orcid.org/0000-0002-9733-8002",
            "contributor_email": "yao.fu@fsu.edu, ",
            "contributor_role": "creator, PI"
        }

    """
    if not contributors_dict:
        return {
            "contributor_name": "",
            "contributor_id": "",
            "contributor_email": "",
            "contributor_role": "",
        }

    # Extract lists in order
    names = []
    ids = []
    emails = []
    roles = []

    # Sort by key to ensure consistent order
    for key in sorted(contributors_dict.keys(), key=lambda x: int(x)):
        contributor = contributors_dict[key]
        names.append(contributor.get("name", ""))
        ids.append(contributor.get("id", ""))
        emails.append(contributor.get("email", ""))
        roles.append(contributor.get("role", ""))

    return {
        "contributor_name": ", ".join(names),
        "contributor_id": ", ".join(ids),
        "contributor_email": ", ".join(emails),
        "contributor_role": ", ".join(roles),
    }


def process_contributor_metadata(
    contributor_name: str,
    contributor_id: str,
    contributor_email: str,
    contributor_role: str,
) -> dict[str, str]:
    """Complete workflow: parse, enrich, and format contributor metadata.

    This is a convenience function that combines all three steps:
    1. Parse comma-separated strings into structured format
    2. Enrich with registry lookups
    3. Format back to comma-separated strings

    Args:
        contributor_name: Comma-separated string of contributor names
        contributor_id: Comma-separated string of contributor IDs/URLs
        contributor_email: Comma-separated string of contributor emails
        contributor_role: Comma-separated string of contributor roles

    Returns
    -------
        Dictionary with processed contributor metadata ready for dataset attributes

    Examples
    --------
        >>> process_contributor_metadata("Yao Fu, Penny Holliday", ",", "yao.fu@fsu.edu", "creator, PI")
        {
            "contributor_name": "Yao Fu, N. Penny Holliday",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, https://orcid.org/0000-0002-9733-8002",
            "contributor_email": "yao.fu@fsu.edu, ",
            "contributor_role": "creator, PI"
        }

    """
    log_debug("Starting contributor metadata processing")

    # Step 1: Parse
    contributors_dict = parse_contributors(
        contributor_name, contributor_id, contributor_email, contributor_role
    )

    # Step 2: Enrich
    enriched_dict = enrich_contributors(contributors_dict)

    # Step 2.5: Deduplicate
    deduplicated_dict = _deduplicate_structured_dict(enriched_dict)

    # Step 3: Format
    result = format_contributors(deduplicated_dict)

    log_debug("Completed contributor metadata processing")
    return result


# Institution handling functions (similar pattern to contributor functions)


def _load_institution_registry() -> dict | None:
    """Load the institution registry from YAML file.

    Returns
    -------
        Dict containing the institution registry, or None if loading fails.

    """
    try:
        registry_file = Path(__file__).parent / "metadata" / "institution_registry.yml"
        with open(registry_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        log_debug(
            f"Loaded institution registry with {len(data.get('institutions', {}))} institutions"
        )
    except (FileNotFoundError, OSError, yaml.YAMLError) as e:
        log_debug(f"Could not load institution registry: {e}")
        return None
    else:
        return data


def _find_institution_by_name(name: str, registry: dict) -> tuple[str, dict] | None:
    """Find an institution in the registry by name variants.

    Args:
        name: The institution name to search for
        registry: The loaded institution registry

    Returns
    -------
        Tuple of (edmo_id, institution_info) if found, None otherwise

    """
    if not registry or not name:
        return None

    institutions = registry.get("institutions", {})
    name_lower = name.lower().strip()

    for edmo_id, institution_info in institutions.items():
        # Check standard name
        if institution_info.get("standard_name", "").lower().strip() == name_lower:
            return edmo_id, institution_info

        # Check name variants
        for variant in institution_info.get("name_variants", []):
            if variant.lower().strip() == name_lower:
                return edmo_id, institution_info

    return None


def parse_institutions(
    contributing_institutions: str,
    contributing_institutions_vocabulary: str,
    contributing_institutions_role: str,
) -> dict[str, dict[str, str]]:
    """Parse comma-separated institution strings into a structured dictionary.

    Args:
        contributing_institutions: Comma-separated string of institution names
        contributing_institutions_vocabulary: Comma-separated string of EDMO URLs
        contributing_institutions_role: Comma-separated string of institution roles

    Returns
    -------
        Dictionary with string keys "1", "2", etc. and values containing
        dictionaries with keys: name, vocabulary, role

    Examples
    --------
        >>> parse_institutions("NOCS, GA Tech", "", "host, partner")
        {
            "1": {"name": "NOCS", "vocabulary": "", "role": "host"},
            "2": {"name": "GA Tech", "vocabulary": "", "role": "partner"}
        }

    """
    # Apply institution corrections to fix formatting issues before parsing
    corrected_institutions = contributing_institutions
    if corrected_institutions:
        for original, corrected in INSTITUTION_CORRECTIONS.items():
            if corrected != original and corrected.startswith(original):
                # Additive correction that appends text (e.g. "(IfM)"). Apply it only
                # where the appended text is not already present, using a negative
                # lookahead — so a plain occurrence is corrected while an
                # already-correct one is not doubled, even within the same string.
                tail = re.escape(corrected[len(original) :])
                corrected_institutions = re.sub(
                    re.escape(original) + f"(?!{tail})",
                    corrected,
                    corrected_institutions,
                )
            else:
                corrected_institutions = corrected_institutions.replace(
                    original, corrected
                )

    # Parse all fields (using corrected institutions string and shared helper)
    names = _split_clean(corrected_institutions)
    vocabularies = _split_clean(contributing_institutions_vocabulary)
    roles = _split_clean(contributing_institutions_role)

    # A single role applies to every listed institution; broadcast it so institutions
    # after the first are not left with an empty role (avoids "host, , ").
    if len(roles) == 1 and len(names) > 1:
        roles = roles * len(names)

    # Find maximum length to determine number of institutions
    # For institutions, we use max length to allow enrichment to fill vocabulary gaps
    max_len = max(len(names), len(vocabularies), len(roles))

    if max_len == 0:
        return {}

    # Build result dictionary
    result = {}
    for i in range(max_len):
        result[str(i + 1)] = {
            "name": names[i] if i < len(names) else "",
            "vocabulary": vocabularies[i] if i < len(vocabularies) else "",
            "role": roles[i] if i < len(roles) else "",
        }

    log_debug(f"Parsed {max_len} institutions from metadata")
    return result


def enrich_institutions(
    institutions_dict: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Enrich institution data using the institution registry.

    This function:
    1. Loads the institution registry
    2. For each institution, tries to find a match by name
    3. Updates the institution with standardized name and EDMO URL if found
    4. Preserves existing data when no registry match is found

    Args:
        institutions_dict: Dictionary from parse_institutions()

    Returns
    -------
        Updated dictionary with enriched institution information

    Examples
    --------
        >>> institutions = {"1": {"name": "NOCS", "vocabulary": "", "role": "host"}}
        >>> enrich_institutions(institutions)
        {"1": {"name": "National Oceanography Centre (Southampton)", "vocabulary": "https://edmo.seadatanet.org/report/17", "role": "host"}}

    """
    registry = _load_institution_registry()
    if not registry:
        log_debug("No institution registry available, returning unchanged data")
        return institutions_dict

    result = {}

    for key, institution in institutions_dict.items():
        updated_institution = institution.copy()
        match_info = None

        # Try to find by name if we have one
        if institution.get("name") and institution["name"].strip():
            match_info = _find_institution_by_name(institution["name"], registry)
            if match_info:
                log_debug(f"Found registry match by name: {institution['name']}")

        # Update institution with registry information if found
        if match_info:
            edmo_id, institution_info = match_info

            # Update name to standardized form
            standard_name = institution_info.get(
                "standard_name", institution.get("name", "")
            )
            updated_institution["name"] = standard_name

            # Update vocabulary URL if not already set
            edmo_url = institution_info.get("id_url", "")
            if (
                not updated_institution.get("vocabulary")
                or not updated_institution["vocabulary"].strip()
            ):
                updated_institution["vocabulary"] = edmo_url

            log_debug(
                f"Enriched institution: '{institution.get('name', '')}' -> '{standard_name}' ({edmo_id})"
            )

        result[key] = updated_institution

    return result


def format_institutions(institutions_dict: dict[str, dict[str, str]]) -> dict[str, str]:
    """Format structured institution data back to comma-separated strings.

    Args:
        institutions_dict: Dictionary from parse_institutions() or enrich_institutions()

    Returns
    -------
        Dictionary with keys: contributing_institutions, contributing_institutions_vocabulary, contributing_institutions_role

    Examples
    --------
        >>> institutions = {
        ...     "1": {"name": "NOC Southampton", "vocabulary": "https://edmo.seadatanet.org/report/17", "role": "host"},
        ...     "2": {"name": "GA Tech", "vocabulary": "https://edmo.seadatanet.org/report/3075", "role": "partner"}
        ... }
        >>> format_institutions(institutions)
        {
            "contributing_institutions": "NOC Southampton, GA Tech",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/17, https://edmo.seadatanet.org/report/3075",
            "contributing_institutions_role": "host, partner"
        }

    """
    if not institutions_dict:
        return {
            "contributing_institutions": "",
            "contributing_institutions_vocabulary": "",
            "contributing_institutions_role": "",
        }

    # Extract lists in order
    names = []
    vocabularies = []
    roles = []

    # Sort by key to ensure consistent order
    for key in sorted(institutions_dict.keys(), key=lambda x: int(x)):
        institution = institutions_dict[key]
        names.append(institution.get("name", ""))
        vocabularies.append(institution.get("vocabulary", ""))
        roles.append(institution.get("role", ""))

    return {
        "contributing_institutions": ", ".join(names),
        "contributing_institutions_vocabulary": ", ".join(vocabularies),
        "contributing_institutions_role": ", ".join(roles),
    }


def process_institution_metadata(
    contributing_institutions: str,
    contributing_institutions_vocabulary: str,
    contributing_institutions_role: str,
) -> dict[str, str]:
    """Complete workflow: parse, enrich, and format institution metadata.

    This is a convenience function that combines all three steps:
    1. Parse comma-separated strings into structured format
    2. Enrich with registry lookups
    3. Format back to comma-separated strings

    Args:
        contributing_institutions: Comma-separated string of institution names
        contributing_institutions_vocabulary: Comma-separated string of EDMO URLs
        contributing_institutions_role: Comma-separated string of institution roles

    Returns
    -------
        Dictionary with processed institution metadata ready for dataset attributes

    Examples
    --------
        >>> process_institution_metadata("NOCS, GA Tech", "", "host, partner")
        {
            "contributing_institutions": "National Oceanography Centre (Southampton), Georgia Institute of Technology",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/17, https://edmo.seadatanet.org/report/3075",
            "contributing_institutions_role": "host, partner"
        }

    """
    log_debug("Starting institution metadata processing")

    # Step 1: Parse
    institutions_dict = parse_institutions(
        contributing_institutions,
        contributing_institutions_vocabulary,
        contributing_institutions_role,
    )

    # Step 2: Enrich
    enriched_dict = enrich_institutions(institutions_dict)

    # Step 2.5: Deduplicate
    deduplicated_dict = _deduplicate_structured_dict(enriched_dict)

    # Step 3: Format
    result = format_institutions(deduplicated_dict)

    log_debug("Completed institution metadata processing")
    return result
