"""Standardisation functions for AMOC observing array datasets.

These functions take raw loaded datasets and:
- Rename variables to standard names
- Add variable-level metadata
- Add or update global attributes
- Prepare datasets for downstream analysis

Currently implemented:
- SAMBA
"""

import xarray as xr
from collections import OrderedDict
import re
from amocarray import logger, utilities
from amocarray.logger import log_debug

log = logger.log  # Use the global logger

# Extracted from OG1.0 spec “## Global attributes” (cf. turn1view0) :contentReference[oaicite:0]{index=0}
_GLOBAL_ATTR_ORDER = [
    "title",
    "platform",
    "platform_vocabulary",
    "id",
    "naming_authority",
    "institution",
    "internal_mission_identifier",
    "geospatial_lat_min",
    "geospatial_lat_max",
    "geospatial_lon_min",
    "geospatial_lon_max",
    "geospatial_vertical_min",
    "geospatial_vertical_max",
    "time_coverage_start",
    "time_coverage_end",
    "site",
    "site_vocabulary",
    "program",
    "program_vocabulary",
    "project",
    "network",
    "contributor_name",
    "contributor_email",
    "contributor_id",
    "contributor_role",
    "contributor_role_vocabulary",
    "contributing_institutions",
    "contributing_institutions_vocabulary",
    "contributing_institutions_role",
    "contributing_institutions_role_vocabulary",
    "uri",
    "data_url",
    "doi",
    "rtqc_method",
    "rtqc_method_doi",
    "web_link",
    "comment",
    "start_date",
    "date_created",
    "featureType",  # preserve this exact case
    "Conventions",  # preserve this exact case
]

_INSTITUTION_CORRECTIONS = {
    "National Oceanography Centre,UK": "National Oceanography Centre (Southampton) (UK)",
    # add more exact‐string fixes here as you discover them
}


def reorder_metadata(attrs: dict) -> dict:
    """
    Return a new dict with keys ordered according to the OG1.0 global‐attribute list.
    Any attrs not in the spec list are appended at the end, in their original order.
    """
    # Shallow copy so we can pop
    remaining = dict(attrs)
    ordered = OrderedDict()

    for key in _GLOBAL_ATTR_ORDER:
        # featureType is case‐sensitive; everything else is matched lowercase
        if key == "featureType":
            if "featureType" in remaining:
                ordered["featureType"] = remaining.pop("featureType")
        else:
            # look for any remaining key whose lower() matches
            to_remove = None
            for orig in remaining:
                if orig.lower() == key:
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
    """
    For each (attr, (value_map, vocab_url)) in `normalizations`:
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


def clean_metadata(attrs: dict, preferred_keys: dict = None) -> dict:
    """
    Clean up a metadata dictionary:
    - Normalize key casing
    - Merge aliases with identical values
    - Apply standard naming (via preferred_keys mapping)
    """
    # Step 0: normalize whitespace everywhere
    attrs = utilities.normalize_whitespace(attrs)

    if preferred_keys is None:
        preferred_keys = {
            "weblink": "web_link",
            "website": "web_link",
            "note": "comment",
            "acknowledgement": "acknowledgement",
            "DOI": "doi",
            "reference": "references",
            "creator": "creator_name",
            "platform_type": "platform",
            "contributor": "contributor_name",
            "Institution": "institution",
            "Project": "project",
            "created_by": "creator_name",
            "principle_investigator": "principal_investigator",
            "principle_investigator_email": "principal_investigator_email",
            "creation_date": "date_created",
        }

    # Step 1: merge any identical aliases first
    merged_attrs = merge_metadata_aliases(attrs, preferred_keys)

    # Step 2: normalize remaining cases and resolve conflicts
    cleaned = {}
    for key, value in merged_attrs.items():
        # key is already canonical if it was an alias
        if key in cleaned:
            if cleaned[key] == value:
                log_debug(f"Skipping identical '{key}'")
                continue
            if len(str(value)) > len(str(cleaned[key])):
                log_debug(
                    f"Replacing '{key}' value with longer one ("
                    f"{len(str(cleaned[key]))}→{len(str(value))} chars)"
                )
                cleaned[key] = value
            else:
                log_debug(f"Keeping existing '{key}', ignoring shorter from merge")
        else:
            cleaned[key] = value

    # Step 3: consolidate contributors and institutions
    cleaned = _consolidate_contributors(cleaned)
    return cleaned


def _consolidate_contributors(cleaned: dict) -> dict:
    """
    Consolidate creators, PIs, publishers, and contributors into unified fields:
    - contributor_name, contributor_role, contributor_email, contributor_id aligned one-to-one
    - contributing_institutions, with placeholders for vocabularies/roles
    """
    log_debug("Starting _consolidate_contributors with attrs: %s", cleaned)

    role_map = {
        "creator_name": "creator",
        "creator": "creator",
        "principal_investigator": "PI",
        "publisher_name": "publisher",
        "publisher": "publisher",
        "contributor_name": "",
        "contributor": "",
    }

    # Step A: extract email & URL buckets
    email_buckets = {}
    url_buckets = {}
    bucket_order = []
    for key in list(cleaned.keys()):
        if key.endswith("_email"):
            raw = cleaned.pop(key)
            parts = [
                v.strip() for v in str(raw).replace(";", ",").split(",") if v.strip()
            ]
            email_buckets[key] = parts
            bucket_order.append(("email", key))
        elif key.endswith("_url"):
            raw = cleaned.pop(key)
            parts = [
                v.strip() for v in str(raw).replace(";", ",").split(",") if v.strip()
            ]
            url_buckets[key] = parts
            bucket_order.append(("url", key))
    log_debug("Email buckets: %s", email_buckets)
    log_debug("URL buckets: %s", url_buckets)

    # Step B: extract names, roles, sources
    names, roles, sources = [], [], []
    for key in list(cleaned.keys()):
        if key in role_map:
            raw = cleaned.pop(key)
            parts = [
                v.strip() for v in str(raw).replace(";", ",").split(",") if v.strip()
            ]
            for p in parts:
                names.append(p)
                roles.append(role_map[key])
                sources.append(key)
    log_debug("Names: %s; Roles: %s; Sources: %s", names, roles, sources)

    # Step C: build contributor fields
    if names:
        # C1: names + roles
        cleaned["contributor_name"] = ", ".join(names)
        cleaned["contributor_role"] = cleaned.get("contributor_role", ", ".join(roles))
        log_debug(
            "Set contributor_name=%r, contributor_role=%r",
            cleaned["contributor_name"],
            cleaned["contributor_role"],
        )

        # C2: align emails one‑to‑one
        aligned_emails = []
        email_copy = {k: v.copy() for k, v in email_buckets.items()}
        for src in sources:
            base = src[:-5] if src.endswith("_name") else src
            ek = f"{base}_email"
            aligned_emails.append(
                email_copy.get(ek, []).pop(0) if email_copy.get(ek) else ""
            )
        cleaned["contributor_email"] = ", ".join(aligned_emails)
        log_debug("Aligned contributor_email=%r", cleaned["contributor_email"])

        # C3: align URLs → contributor_id
        aligned_ids = []
        url_copy = {k: v.copy() for k, v in url_buckets.items()}
        for src in sources:
            base = src[:-5] if src.endswith("_name") else src
            uk = f"{base}_url"
            aligned_ids.append(url_copy.get(uk, []).pop(0) if url_copy.get(uk) else "")
        cleaned["contributor_id"] = ", ".join(aligned_ids)
        log_debug("Aligned contributor_id=%r", cleaned["contributor_id"])

    elif bucket_order:
        # Email-only (or URL-only) fallback
        # Build flat lists preserving email/url order
        flat_emails, flat_ids, placeholder_roles = [], [], []
        for typ, bk in bucket_order:
            role = role_map.get(bk.rsplit("_", 1)[0], "")
            if typ == "email":
                for e in email_buckets.get(bk, []):
                    flat_emails.append(e)
                    placeholder_roles.append(role)
            else:  # typ == "url"
                for u in url_buckets.get(bk, []):
                    flat_ids.append(u)
                    # ensure a role slot for each URL too
                    placeholder_roles.append(role)

        cleaned["contributor_name"] = ", ".join([""] * len(placeholder_roles))
        cleaned["contributor_role"] = ", ".join(placeholder_roles)
        cleaned["contributor_email"] = ", ".join(flat_emails)
        cleaned["contributor_id"] = ", ".join(flat_ids)
        log_debug("Placeholder contributor_email=%r", cleaned["contributor_email"])
        log_debug("Placeholder contributor_id=%r", cleaned["contributor_id"])

    # Step D: consolidate institution keys
    inst_vocab_map = {
        "national oceanography centre (southampton) (uk)": "https://edmo.seadatanet.org/report/17",
        "helmholtz centre for ocean research kiel (geomar)": "https://edmo.seadatanet.org/report/2947",
        # add more lower‐cased, normalized keys here...
    }
    # Build normalized lookup (keys are already whitespace‑cleaned and casefolded)
    inst_vocab_norm = {
        re.sub(r"\s+", " ", key.casefold().strip()): url
        for key, url in inst_vocab_map.items()
    }
    for raw_key, url in inst_vocab_map.items():
        k2 = re.sub(r"\s+", " ", raw_key.replace("\u00A0", " ")).strip().lower()
        k2 = " ".join(raw_key.strip().casefold().split())
        inst_vocab_norm[k2] = url

        insts = []
        inst_vocabs = []
        for attr_key in list(cleaned.keys()):
            if attr_key.lower() in (
                "institution",
                "publisher_institution",
                "contributor_institution",
            ):
                raw_inst = cleaned.pop(attr_key)

                # apply any known corrections
                fixed = _INSTITUTION_CORRECTIONS.get(raw_inst, raw_inst)

                # split on semicolons only (commas inside names are preserved)
                if ";" in fixed:
                    parts = [p.strip() for p in fixed.split(";") if p.strip()]
                else:
                    parts = [fixed.strip()]

                for inst in parts:
                    # normalize for lookup
                    lookup = re.sub(r"\s+", " ", inst.casefold().strip())

                    # try exact match
                    url = inst_vocab_norm.get(lookup, "")

                    # fallback: substring match
                    if not url:
                        for k_norm, v in inst_vocab_norm.items():
                            if lookup == k_norm or lookup in k_norm:
                                url = v
                                break

                    insts.append(inst)
                    inst_vocabs.append(url)
                    log_debug("Matched institution %r → %r → %r", inst, lookup, url)

        if insts:
            # dedupe institutions, preserving order
            unique_insts = list(dict.fromkeys(insts))
            # align vocab list to those unique insts
            seen = set()
            unique_vocabs = []
            for inst, url in zip(insts, inst_vocabs):
                if inst not in seen:
                    seen.add(inst)
                    unique_vocabs.append(url)

            cleaned["contributing_institutions"] = ", ".join(unique_insts)
            cleaned["contributing_institutions_vocabulary"] = ", ".join(unique_vocabs)
            cleaned.setdefault("contributing_institutions_role", "")
            cleaned.setdefault("contributing_institutions_role_vocabulary", "")
    log_debug("Finished _consolidate_contributors: %s", cleaned)
    return cleaned


def merge_metadata_aliases(attrs: dict, preferred_keys: dict) -> dict:
    """
    Consolidate and rename metadata keys case‑insensitively (except featureType),
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
            # 1) if we have a mapping for this lowercase alias, rename
            if low in preferred_keys:
                canonical = preferred_keys[low]
            # 2) otherwise use the lowercased key
            else:
                canonical = low

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


def standardise_samba(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="samba")


def standardise_rapid(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="rapid")


def standardise_move(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="move")


def standardise_osnap(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="osnap")


def standardise_fw2015(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="fw2015")


def standardise_mocha(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="mocha")


def standardise_41n(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="41n")


def standardise_dso(ds: xr.Dataset, file_name: str) -> xr.Dataset:
    return standardise_array(ds, file_name, array_name="dso")


def standardise_array(ds: xr.Dataset, file_name: str, array_name: str) -> xr.Dataset:
    """Standardise a mooring array dataset using YAML-based metadata.

    Parameters
    ----------
    ds : xr.Dataset
        Raw dataset loaded from a reader.
    file_name : str
        Filename (e.g., 'moc_transports.nc') expected to match ds.attrs["source_file"].
    array_name : str
        Name of the mooring array (e.g., 'samba', 'rapid', 'move', 'osnap', 'fw2015', 'mocha').

    Returns
    -------
    xr.Dataset
        Standardised dataset with renamed variables and enriched metadata.

    Raises
    ------
    ValueError
        If file_name does not match ds.attrs["source_file"].
    """
    # 1) Validate source_file matches
    src = ds.attrs.get("source_file")
    if src and src != file_name:
        raise ValueError(f"file_name {file_name!r} ≠ ds.attrs['source_file'] {src!r}")
    log_debug(f"Standardising {file_name} for {array_name.upper()}")

    # 2) Collect new attrs from YAML
    meta = utilities.load_array_metadata(array_name)
    file_meta = meta["files"].get(file_name, {})

    # Rename variables
    rename_dict = file_meta.get("variable_mapping", {})
    ds = ds.rename(rename_dict)

    # Apply per-variable metadata
    var_meta = file_meta.get("variables", {})
    for var_name, attrs in var_meta.items():
        if var_name in ds.variables:
            ds[var_name].attrs.update(attrs)

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

    # 3) Merge existing attrs + new global attrs + file-specific
    combined = {}
    combined.update(ds.attrs)  # original reader attrs
    combined.update(meta.get("metadata", {}))  # array‑level
    combined.update(
        {
            "summary": meta["metadata"].get("description", ""),
            "weblink": meta["metadata"].get("weblink", ""),
        }
    )
    combined.update(
        {k: file_meta[k] for k in ("acknowledgement", "data_product") if k in file_meta}
    )

    # 4) Clean up collisions & override ds.attrs wholesale
    cleaned = clean_metadata(combined)

    # 5) Normalize and add vocabularies
    normalizations = {
        "platform": (
            {"Mooring array": "mooring"},
            "https://vocab.nerc.ac.uk/collection/L06/",
        ),
        "featureType": (
            {"timeSeries": "timeSeries"},
            "https://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#_features_and_feature_types",
        ),
        # add more fields here as needed
    }
    cleaned = normalize_and_add_vocabulary(cleaned, normalizations)

    # 6) Reorder metadata according
    ds.attrs = cleaned
    ds.attrs = reorder_metadata(ds.attrs)
    #    ds = utilities.safe_update_attrs(ds, cleaned, overwrite=False)
    return ds
