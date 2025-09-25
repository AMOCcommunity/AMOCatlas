import pytest
from amocatlas import logger, readers, standardise, utilities

logger.disable_logging()


def test_standardise_samba():
    # Load datasets (could be one or two files)
    datasets = readers.load_dataset("samba")

    # Load metadata from the YAML to match expectations
    meta = utilities.load_array_metadata("samba")
    global_meta = meta["metadata"]
    file_metas = meta["files"]

    for ds in datasets:
        file_name = ds.attrs.get("source_file")
        assert file_name in file_metas, f"Missing metadata for file: {file_name}"

        # Standardise the dataset
        std_ds = standardise.standardise_samba(ds, file_name)

        # Global metadata keys expected
        for key in ["web_link", "summary"]:
            assert key in std_ds.attrs, f"Missing global attribute: {key}"

        # Check if data_product or acknowledgement were added if in the YAML
        for key in ["data_product", "acknowledgement"]:
            if key in file_metas[file_name]:
                assert key in std_ds.attrs

        # Variables renamed and enriched
        variable_mapping = file_metas[file_name].get("variable_mapping", {})
        expected_vars = list(variable_mapping.values())

        for var in expected_vars:
            assert var in std_ds.variables, f"Expected variable not found: {var}"
            attrs = std_ds[var].attrs
            for attr in ["units", "standard_name"]:
                assert attr in attrs, f"Missing {attr} for variable: {var}"


# Only include mappings where alias != canonical key
PREFERRED_KEYS = {
    "title": "summary",
    "weblink": "web_link",
    "note": "comment",
    "Acknowledgement": "acknowledgement",
    "DOI": "doi",
    "Reference": "references",
    "Creator": "creator_name",
    "Created_by": "creator_name",
    "Creation_date": "date_created",
}


@pytest.mark.parametrize(
    "attrs,expected",
    [
        # identical values should collapse into one with the canonical key
        (
            {"DOI": "10", "doi": "10", "Title": "Test", "title": "Test"},
            {"doi": "10", "summary": "Test"},
        ),
        # conflicting values: keep the first seen ('DOI' in this case)
        (
            {"DOI": "10", "doi": "20"},
            {"doi": "10"},
        ),
        # no aliases: all keys preserved
        (
            {"foo": "1", "bar": "2"},
            {"foo": "1", "bar": "2"},
        ),
        # mix of alias and unique
        (
            {"Acknowledgement": "Ack", "acknowledgement": "Ack", "note": "Note"},
            {"acknowledgement": "Ack", "comment": "Note"},
        ),
    ],
)
def test_merge_metadata_aliases(attrs, expected):
    """
    Test that merge_metadata_aliases:
    - Collapses identical aliases into the canonical key.
    - Keeps first value when conflicts occur.
    - Leaves non-alias keys untouched.
    """
    result = standardise.merge_metadata_aliases(attrs, PREFERRED_KEYS)
    assert result == expected


@pytest.mark.parametrize(
    "input_dict, expected_dict",
    [
        (
            {
                "creator_name": "Alice",
                "principal_investigator": "Bob",
                "publisher_name": "Carol",
                "institution": "InstA",
                "publisher_institution": "InstB;InstC",
            },
            {
                "contributor_name": "Alice, Bob, Carol",
                "contributor_role": "creator, PI, publisher",
                "contributing_institutions": "InstA, InstB, InstC",
                "contributing_institutions_vocabulary": ", , ",
                "contributing_institutions_role": "",
                "contributing_institutions_role_vocabulary": "",
                "contributor_email": ", , ",
                "contributor_id": ", , ",
            },
        ),
        (
            {
                "creator_email": "alice@example.com",
                "principal_investigator_email": "bob1@example.com; bob2@example.com",
                "publisher_email": "carol@example.com",
            },
            {
                "contributor_name": ", , , ",
                "contributor_email": "alice@example.com, bob1@example.com, bob2@example.com, carol@example.com",
                "contributor_role": "creator, PI, PI, publisher",
                "contributor_id": "",
            },
        ),
        (
            {
                "creator_name": "Alice",
                "principal_investigator": "Bob",
                "principal_investigator_email": "pi@inst.org",
            },
            {
                "contributor_name": "Alice, Bob",
                "contributor_role": "creator, PI",
                "contributor_email": ", pi@inst.org",
                "contributor_id": ", ",
            },
        ),
    ],
)
def test_consolidate_contributors_merges_and_assigns_roles(input_dict, expected_dict):
    """
    _consolidate_contributors should:
    - Merge name fields (creator, principal_investigator, publisher, contributor)
    - Assign roles based on source key mapping
    - Merge institution fields into contributing_institutions
    - Merge email fields into contributor_email
    - Add vocabulary and role placeholder keys for institutions
    """
    data = input_dict.copy()  # avoid mutating input
    result = standardise._consolidate_contributors(data)
    assert result == expected_dict
