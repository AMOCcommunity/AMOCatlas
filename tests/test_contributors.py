"""Tests for contributor metadata handling functions.

These tests cover the modular approach to parsing, enriching, and formatting
contributor metadata with registry lookups and standardization.
"""

import pytest

from amocatlas import contributors


class TestParseContributors:
    """Test parsing comma-separated contributor strings into structured format."""

    def test_complete_fields(self):
        """Test parsing when all fields are complete."""
        names = "Yao Fu, Penny Holliday"
        ids = ","
        emails = "yao.fu@fsu.edu,"
        roles = "creator, PI"

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "",
                "role": "creator",
            },
            "2": {"name": "Penny Holliday", "email": "", "id": "", "role": "PI"},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_only_names(self):
        """Test parsing with only names provided."""
        names = "Yao Fu, Penny Holliday"
        ids = ""
        emails = ""
        roles = ""

        expected = {
            "1": {"name": "Yao Fu", "email": "", "id": "", "role": ""},
            "2": {"name": "Penny Holliday", "email": "", "id": "", "role": ""},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_only_ids(self):
        """Test parsing with only IDs provided (names should be empty)."""
        names = ""
        ids = "https://orcid.org/0000-0003-2227-3694,https://orcid.org/0000-0002-9733-8002"
        emails = ""
        roles = ""

        expected = {
            "1": {
                "name": "",
                "email": "",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "",
            },
            "2": {
                "name": "",
                "email": "",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "",
            },
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_mismatched_lengths(self):
        """Fields shorter than the name list pad with empty strings, EXCEPT a single role,
        which broadcasts to every contributor (one role for a list of people means they all
        share it). Per-person fields (id, email) still pad positionally.
        """
        names = "Yao Fu, Penny Holliday, Brian King"
        ids = "https://orcid.org/0000-0003-2227-3694"
        emails = "yao.fu@fsu.edu, penny@example.com"
        roles = "creator"

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "creator",
            },
            "2": {
                "name": "Penny Holliday",
                "email": "penny@example.com",
                "id": "",
                "role": "creator",
            },
            "3": {"name": "Brian King", "email": "", "id": "", "role": "creator"},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_empty_input(self):
        """Test parsing with all empty inputs."""
        result = contributors.parse_contributors("", "", "", "")
        assert result == {}

    def test_whitespace_handling(self):
        """Test that extra whitespace is properly stripped."""
        names = " Yao Fu , Penny Holliday "
        ids = " , "
        emails = " yao.fu@fsu.edu , "
        roles = " creator , PI "

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "",
                "role": "creator",
            },
            "2": {"name": "Penny Holliday", "email": "", "id": "", "role": "PI"},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_single_word_name_warns_possible_last_first_split(self):
        """A single-word parsed name warns about a possible 'Last, First' split."""
        with pytest.warns(UserWarning, match="single word"):
            result = contributors.parse_contributors("Moat, Ben I.", "", "", "")
        # Behaviour is unchanged: the comma still splits into two entries.
        assert result["1"]["name"] == "Moat"
        assert result["2"]["name"] == "Ben I."

    def test_multiword_names_do_not_warn(self):
        """Ordinary 'First Last' contributor lists produce no warning."""
        import warnings as _warnings

        with _warnings.catch_warnings():
            _warnings.simplefilter("error")
            contributors.parse_contributors("Yao Fu, Penny Holliday", "", "", "")


class TestEnrichContributors:
    """Test enriching contributor data with registry lookups."""

    def test_successful_registry_lookup(self):
        """Test successful lookup of contributors in registry."""
        contributors_dict = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "",
                "role": "creator",
            },
            "2": {"name": "Penny Holliday", "email": "", "id": "", "role": "PI"},
        }

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "creator",
            },
            "2": {
                "name": "N. Penny Holliday",
                "email": "",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "PI",
            },
        }

        result = contributors.enrich_contributors(contributors_dict)
        assert result == expected

    def test_no_registry_matches(self):
        """Test when no contributors are found in registry."""
        contributors_dict = {
            "1": {
                "name": "Unknown Person",
                "email": "unknown@example.com",
                "id": "",
                "role": "creator",
            },
            "2": {"name": "Another Unknown", "email": "", "id": "", "role": "PI"},
        }

        # Should return unchanged (no matches in registry)
        result = contributors.enrich_contributors(contributors_dict)
        assert result == contributors_dict

    def test_partial_registry_matches(self):
        """Test when only some contributors are found in registry."""
        contributors_dict = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "",
                "role": "creator",
            },
            "2": {"name": "Unknown Person", "email": "", "id": "", "role": "PI"},
        }

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "creator",
            },
            "2": {
                "name": "Unknown Person",
                "email": "",
                "id": "",
                "role": "PI",
            },  # Unchanged
        }

        result = contributors.enrich_contributors(contributors_dict)
        assert result == expected

    def test_existing_id_replaced_with_orcid(self):
        """Test that existing non-ORCID IDs are replaced with registry ORCID."""
        contributors_dict = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://example.com/existing-id",
                "role": "creator",
            }
        }

        # Should replace existing ID with registry ORCID
        expected = {
            "1": {
                "name": "Yao Fu",  # Registry lookup enriches the name and ID
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",  # Registry ORCID
                "role": "creator",
            }
        }
        result = contributors.enrich_contributors(contributors_dict)
        assert result == expected

    def test_genuine_orcid_not_overwritten_by_non_orcid_placeholder(self):
        """A genuine incoming ORCID survives a registry entry with a non-ORCID id_url."""
        # Rebecca Woodgate's registry id_url is a lab webpage, not an ORCID.
        genuine_orcid = "https://orcid.org/0000-0002-1234-5678"
        contributors_dict = {
            "1": {"name": "R. Woodgate", "email": "", "id": genuine_orcid, "role": "PI"}
        }
        result = contributors.enrich_contributors(contributors_dict)
        # Name is standardised from the registry, but the genuine ORCID is kept.
        assert result["1"]["name"] == "Rebecca Woodgate"
        assert result["1"]["id"] == genuine_orcid

    def test_non_orcid_registry_id_used_when_no_incoming_id(self):
        """With no incoming id, a non-ORCID registry id_url is used as a fallback."""
        contributors_dict = {
            "1": {"name": "R. Woodgate", "email": "", "id": "", "role": "PI"}
        }
        result = contributors.enrich_contributors(contributors_dict)
        assert result["1"]["name"] == "Rebecca Woodgate"
        assert "orcid.org/" not in result["1"]["id"]
        assert result["1"]["id"] == (
            "https://psc.apl.uw.edu/people/investigators/rebecca-woodgate/"
        )

    def test_is_orcid_url_anchors_on_host(self):
        """_is_orcid_url matches genuine orcid.org URLs, not substring lookalikes."""
        assert contributors._is_orcid_url("https://orcid.org/0000-0002-1234-5678")
        assert contributors._is_orcid_url("http://orcid.org/0000-0002-1234-5678")
        assert contributors._is_orcid_url("https://www.orcid.org/0000-0002-1234-5678")
        # Lookalikes that merely contain the substring must be rejected.
        assert not contributors._is_orcid_url(
            "https://notorcid.org/0000-0002-1234-5678"
        )
        assert not contributors._is_orcid_url("https://example.com/?ref=orcid.org/x")
        assert not contributors._is_orcid_url("")
        assert not contributors._is_orcid_url(None)

    def test_id_only_lookup(self):
        """Test lookup when starting with only IDs (names empty)."""
        contributors_dict = {
            "1": {
                "name": "",
                "email": "",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "",
            },
            "2": {
                "name": "",
                "email": "",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "",
            },
        }

        expected = {
            "1": {
                "name": "Yao Fu",
                "email": "",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "",
            },
            "2": {
                "name": "N. Penny Holliday",
                "email": "",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "",
            },
        }

        result = contributors.enrich_contributors(contributors_dict)
        assert result == expected


class TestFormatContributors:
    """Test formatting contributor dictionaries back to comma-separated strings."""

    def test_format_complete_data(self):
        """Test formatting complete contributor data."""
        contributors_dict = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "creator",
            },
            "2": {
                "name": "N. Penny Holliday",
                "email": "",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "PI",
            },
        }

        expected = {
            "contributor_name": "Yao Fu, N. Penny Holliday",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, https://orcid.org/0000-0002-9733-8002",
            "contributor_email": "yao.fu@fsu.edu, ",
            "contributor_role": "creator, PI",
        }

        result = contributors.format_contributors(contributors_dict)
        assert result == expected

    def test_format_empty_dict(self):
        """Test formatting empty contributor dictionary."""
        expected = {
            "contributor_name": "",
            "contributor_id": "",
            "contributor_email": "",
            "contributor_role": "",
        }

        result = contributors.format_contributors({})
        assert result == expected

    def test_format_single_contributor(self):
        """Test formatting single contributor."""
        contributors_dict = {
            "1": {
                "name": "Yao Fu",
                "email": "yao.fu@fsu.edu",
                "id": "https://orcid.org/0000-0003-2227-3694",
                "role": "creator",
            }
        }

        expected = {
            "contributor_name": "Yao Fu",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694",
            "contributor_email": "yao.fu@fsu.edu",
            "contributor_role": "creator",
        }

        result = contributors.format_contributors(contributors_dict)
        assert result == expected

    def test_format_partial_data(self):
        """Test formatting when some fields are empty."""
        contributors_dict = {
            "1": {"name": "Yao Fu", "email": "", "id": "", "role": "creator"},
            "2": {
                "name": "",
                "email": "penny@example.com",
                "id": "https://orcid.org/0000-0002-9733-8002",
                "role": "",
            },
        }

        expected = {
            "contributor_name": "Yao Fu, ",
            "contributor_id": ", https://orcid.org/0000-0002-9733-8002",
            "contributor_email": ", penny@example.com",
            "contributor_role": "creator, ",
        }

        result = contributors.format_contributors(contributors_dict)
        assert result == expected


class TestWorkflowIntegration:
    """Test the complete workflow from parsing through enrichment to formatting."""

    def test_example_1_complete_workflow(self):
        """Test example 1: 'Yao Fu, Penny Holliday' with partial fields."""
        # Input
        names = "Yao Fu, Penny Holliday"
        ids = ","
        emails = "yao.fu@fsu.edu"
        roles = "creator, PI"

        # Expected output
        expected = {
            "contributor_name": "Yao Fu, N. Penny Holliday",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, https://orcid.org/0000-0002-9733-8002",
            "contributor_email": "yao.fu@fsu.edu, ",
            "contributor_role": "creator, PI",
        }

        # Workflow
        parsed = contributors.parse_contributors(names, ids, emails, roles)
        enriched = contributors.enrich_contributors(parsed)
        result = contributors.format_contributors(enriched)

        assert result == expected

    def test_example_2_id_only_workflow(self):
        """Test example 2: Starting with only IDs."""
        # Input
        names = ""
        ids = "https://orcid.org/0000-0003-2227-3694,https://orcid.org/0000-0002-9733-8002"
        emails = ""
        roles = ""

        # Expected output
        expected = {
            "contributor_name": "Yao Fu, N. Penny Holliday",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, https://orcid.org/0000-0002-9733-8002",
            "contributor_email": ", ",
            "contributor_role": ", ",
        }

        # Workflow
        parsed = contributors.parse_contributors(names, ids, emails, roles)
        enriched = contributors.enrich_contributors(parsed)
        result = contributors.format_contributors(enriched)

        assert result == expected

    def test_no_registry_matches_workflow(self):
        """Test workflow when no contributors are found in registry."""
        # Input
        names = "Unknown Person, Another Unknown"
        ids = ","
        emails = "unknown@example.com"
        roles = "creator, PI"

        # Expected output (unchanged since no registry matches)
        expected = {
            "contributor_name": "Unknown Person, Another Unknown",
            "contributor_id": ", ",
            "contributor_email": "unknown@example.com, ",
            "contributor_role": "creator, PI",
        }

        # Workflow
        parsed = contributors.parse_contributors(names, ids, emails, roles)
        enriched = contributors.enrich_contributors(parsed)
        result = contributors.format_contributors(enriched)

        assert result == expected

    def test_mixed_registry_matches_workflow(self):
        """Test workflow with some registry matches and some unknowns."""
        # Input
        names = "Yao Fu, Unknown Person, Brian King"
        ids = ",,"
        emails = "yao.fu@fsu.edu,unknown@example.com,"
        roles = "creator, contributor, PI"

        # Expected output
        expected = {
            "contributor_name": "Yao Fu, Unknown Person, Brian King",
            "contributor_id": "https://orcid.org/0000-0003-2227-3694, , https://orcid.org/0000-0003-1338-3234",
            "contributor_email": "yao.fu@fsu.edu, unknown@example.com, ",
            "contributor_role": "creator, contributor, PI",
        }

        # Workflow
        parsed = contributors.parse_contributors(names, ids, emails, roles)
        enriched = contributors.enrich_contributors(parsed)
        result = contributors.format_contributors(enriched)

        assert result == expected


class TestHelperFunctions:
    """Test any helper functions in the contributors module."""

    def test_split_comma_string(self):
        """Test the helper function for splitting comma-separated strings."""
        # This test depends on the implementation - adjust as needed
        test_string = "item1, item2, item3"

        # Assuming there's a helper function like this:
        # result = contributors._split_comma_string(test_string)
        # assert result == expected

        # For now, we'll test the behavior implicitly through parse_contributors
        result = contributors.parse_contributors(test_string, "", "", "")
        assert len(result) == 3
        assert result["1"]["name"] == "item1"
        assert result["2"]["name"] == "item2"
        assert result["3"]["name"] == "item3"

    def test_empty_string_handling(self):
        """Test handling of empty and whitespace-only strings."""
        empty_cases = ["", "   ", "\t", "\n"]

        for empty_case in empty_cases:
            result = contributors.parse_contributors(empty_case, "", "", "")
            assert result == {}


class TestInstitutionHandling:
    """Test institution metadata handling functions."""

    def test_single_institution_with_standardization(self):
        """Test single institution lookup and standardization."""
        # Input: NOC with variation name, no vocabulary
        institutions = "National Oceanography Centre Southampton"
        vocabularies = ""
        roles = ""

        # Expected: standardized name with EDMO URL (using your test specification)
        expected = {
            "contributing_institutions": "National Oceanography Centre (Southampton)",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/17",
            "contributing_institutions_role": "",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_multiple_institutions_with_standardization(self):
        """Test multiple institution lookup with known abbreviations."""
        # Input: NOCS + GA Tech abbreviations
        institutions = "NOCS, GA Tech"
        vocabularies = ""
        roles = ""

        # Expected: both institutions standardized with EDMO URLs
        expected = {
            "contributing_institutions": "National Oceanography Centre (Southampton), Georgia Institute of Technology",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/17, https://edmo.seadatanet.org/report/3075",
            "contributing_institutions_role": ", ",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_institutions_with_roles(self):
        """Test institutions with corresponding roles."""
        institutions = "WHOI, GEOMAR"
        vocabularies = ""
        roles = "datacenter, collaborator"

        expected = {
            "contributing_institutions": "Woods Hole Oceanographic Institution, Helmholtz Centre for Ocean Research Kiel (GEOMAR)",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/3844, https://edmo.seadatanet.org/report/2947",
            "contributing_institutions_role": "datacenter, collaborator",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_additive_correction_not_doubled(self):
        """An institution already carrying '(IfM)' is not corrected twice."""
        # calafat2025 ships this exact _overwrite value; the substring correction
        # used to turn the trailing entry into "University of Hamburg (IfM) (IfM)".
        institutions = (
            "National Oceanography Centre (Liverpool), "
            "University of the Balearic Islands, University of Hamburg (IfM)"
        )
        result = contributors.process_institution_metadata(institutions, "", "")
        joined = result["contributing_institutions"]
        assert "(IfM) (IfM)" not in joined
        assert joined.count("University of Hamburg (IfM)") == 1

    def test_plain_name_still_corrected_once(self):
        """A plain 'University of Hamburg' still gains '(IfM)' exactly once."""
        result = contributors.process_institution_metadata(
            "University of Hamburg", "", ""
        )
        assert result["contributing_institutions"] == "University of Hamburg (IfM)"

    def test_additive_correction_fixes_plain_and_keeps_corrected(self):
        """A string mixing a plain and an already-suffixed name: plain gains the suffix
        (once), the suffixed one is not doubled.
        """
        # parse_institutions runs the correction before de-duplication, so both entries
        # are visible here (process_institution_metadata would collapse the duplicates).
        result = contributors.parse_institutions(
            "University of Hamburg, University of Hamburg (IfM)", "", ""
        )
        names = [entry["name"] for entry in result.values()]
        assert names == ["University of Hamburg (IfM)", "University of Hamburg (IfM)"]
        assert all("(IfM) (IfM)" not in name for name in names)

    def test_single_role_broadcast_to_all_institutions(self):
        """A single role is applied to every institution, not just the first."""
        result = contributors.process_institution_metadata(
            "WHOI, GEOMAR, SIO", "", "host"
        )
        assert result["contributing_institutions_role"] == "host, host, host"

    def test_unknown_institutions(self):
        """Test institutions not found in registry."""
        institutions = "Unknown University, Another Unknown Org"
        vocabularies = ""
        roles = "host, partner"

        # Should preserve original names when not found in registry
        expected = {
            "contributing_institutions": "Unknown University, Another Unknown Org",
            "contributing_institutions_vocabulary": ", ",
            "contributing_institutions_role": "host, partner",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_mixed_known_unknown_institutions(self):
        """Test mix of known and unknown institutions."""
        institutions = "SIO, Unknown Research Center, AWI"
        vocabularies = ""
        roles = "data provider, collaborator, analysis"

        expected = {
            "contributing_institutions": "Scripps Institution of Oceanography, Unknown Research Center, Alfred Wegener Institute (AWI)",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/1390, , https://edmo.seadatanet.org/report/1368",
            "contributing_institutions_role": "data provider, collaborator, analysis",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_existing_vocabularies_preserved(self):
        """Test that existing vocabularies are preserved when provided."""
        institutions = "Custom Institution Name"
        vocabularies = "https://custom.edmo.url/12345"
        roles = "publisher"

        # Should keep existing vocabulary URL even if institution not in registry
        expected = {
            "contributing_institutions": "Custom Institution Name",
            "contributing_institutions_vocabulary": "https://custom.edmo.url/12345",
            "contributing_institutions_role": "publisher",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected

    def test_empty_input(self):
        """Test handling of empty inputs."""
        result = contributors.process_institution_metadata("", "", "")
        expected = {
            "contributing_institutions": "",
            "contributing_institutions_vocabulary": "",
            "contributing_institutions_role": "",
        }
        assert result == expected

    def test_mismatched_field_lengths(self):
        """Test handling when field lengths don't match."""
        institutions = "NOCS, WHOI, SIO"  # Use NOCS instead of ambiguous NOC
        vocabularies = "https://custom.url"  # Only one vocabulary for 3 institutions
        roles = "host, collaborator"  # Only 2 roles for 3 institutions

        expected = {
            "contributing_institutions": "National Oceanography Centre (Southampton), Woods Hole Oceanographic Institution, Scripps Institution of Oceanography",
            "contributing_institutions_vocabulary": "https://custom.url, https://edmo.seadatanet.org/report/3844, https://edmo.seadatanet.org/report/1390",
            "contributing_institutions_role": "host, collaborator, ",
        }

        result = contributors.process_institution_metadata(
            institutions, vocabularies, roles
        )
        assert result == expected


class TestInstitutionWorkflowIntegration:
    """Test the complete institution workflow."""

    def test_parse_enrich_format_workflow(self):
        """Test the complete parse -> enrich -> format workflow for institutions."""
        # Test individual functions work together
        parsed = contributors.parse_institutions("NOCS, GA Tech", "", "host, partner")

        expected_parsed = {
            "1": {"name": "NOCS", "vocabulary": "", "role": "host"},
            "2": {"name": "GA Tech", "vocabulary": "", "role": "partner"},
        }
        assert parsed == expected_parsed

        enriched = contributors.enrich_institutions(parsed)

        expected_enriched = {
            "1": {
                "name": "National Oceanography Centre (Southampton)",
                "vocabulary": "https://edmo.seadatanet.org/report/17",
                "role": "host",
            },
            "2": {
                "name": "Georgia Institute of Technology",
                "vocabulary": "https://edmo.seadatanet.org/report/3075",
                "role": "partner",
            },
        }
        assert enriched == expected_enriched

        formatted = contributors.format_institutions(enriched)

        expected_formatted = {
            "contributing_institutions": "National Oceanography Centre (Southampton), Georgia Institute of Technology",
            "contributing_institutions_vocabulary": "https://edmo.seadatanet.org/report/17, https://edmo.seadatanet.org/report/3075",
            "contributing_institutions_role": "host, partner",
        }
        assert formatted == expected_formatted


class TestDelimiterSupport:
    """Test support for different delimiter types in contributor parsing."""

    def test_semicolon_delimited_contributors(self):
        """Test parsing semicolon-delimited contributors."""
        names = "Simon Wett; Monika Rhein; Dagmar Kieke"
        ids = ""
        emails = ""
        roles = ""

        expected = {
            "1": {"name": "Simon Wett", "email": "", "id": "", "role": ""},
            "2": {"name": "Monika Rhein", "email": "", "id": "", "role": ""},
            "3": {"name": "Dagmar Kieke", "email": "", "id": "", "role": ""},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_mixed_delimiters_contributors(self):
        """Test parsing contributors with mixed comma and semicolon delimiters."""
        names = "Simon Wett, Monika Rhein, Dagmar Kieke; Hannah Nowitzki"
        ids = ""
        emails = ""
        roles = ""

        expected = {
            "1": {"name": "Simon Wett", "email": "", "id": "", "role": ""},
            "2": {"name": "Monika Rhein", "email": "", "id": "", "role": ""},
            "3": {"name": "Dagmar Kieke", "email": "", "id": "", "role": ""},
            "4": {"name": "Hannah Nowitzki", "email": "", "id": "", "role": ""},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_complex_mixed_delimiters(self):
        """Test complex mixing of delimiters with corresponding IDs."""
        names = "A; B, C; D"
        ids = "id1; id2, id3; id4"
        emails = "e1; e2, e3; e4"
        roles = "r1; r2, r3; r4"

        expected = {
            "1": {"name": "A", "email": "e1", "id": "id1", "role": "r1"},
            "2": {"name": "B", "email": "e2", "id": "id2", "role": "r2"},
            "3": {"name": "C", "email": "e3", "id": "id3", "role": "r3"},
            "4": {"name": "D", "email": "e4", "id": "id4", "role": "r4"},
        }

        result = contributors.parse_contributors(names, ids, emails, roles)
        assert result == expected

    def test_misaligned_fields_handling(self):
        """Test that misaligned contributor fields are handled gracefully."""
        # Simulate what happens in standardise.py when emails are extended
        names = "John Doe, Jane Smith"
        ids = "id1, id2"
        emails = ", , extra1@email.com, extra2@email.com"  # Leading empty values
        roles = "creator, PI"

        result = contributors.parse_contributors(names, ids, emails, roles)

        # Should parse all entries based on maximum field length
        assert len(result) == 4  # Maximum of all field lengths

        # Check that first two entries have names
        assert result["1"]["name"] == "John Doe"
        assert result["2"]["name"] == "Jane Smith"

        # Check that last two entries have only emails
        assert result["3"]["name"] == ""
        assert result["3"]["email"] == "extra1@email.com"
        assert result["4"]["name"] == ""
        assert result["4"]["email"] == "extra2@email.com"

        # Formatting should preserve all entries
        formatted = contributors.format_contributors(result)

        # Names and roles will have trailing empty values (this is acceptable)
        assert formatted["contributor_name"] == "John Doe, Jane Smith, , "
        assert formatted["contributor_role"] == "creator, PI, , "

        # Emails will have leading empty values (this is acceptable)
        assert (
            formatted["contributor_email"] == ", , extra1@email.com, extra2@email.com"
        )

    def test_osnap_email_alignment_issue(self):
        """Test the actual OSNAP data structure that causes email misalignment."""
        # Simulate the three-phase processing with OSNAP raw data
        from amocatlas.standardise import _consolidate_contributors

        # Raw OSNAP metadata structure (simplified)
        raw_attrs = {
            "creator_name": "OSNAP investigators",
            "contributor_name": "Yao Fu, M. Susan Lozier, Amy Bower, Kristin Burmeister, Tiago Carrilho Biló, Frederic Cyr, Stuart A. Cunningham, Brad deYoung, Ahmad Fehmi Dilmahamod, M. Femke de Jong, Nora Fried, N. Penny Holliday, Neil Fraser, William E. Johns, Feili Li, Johannes Karstensen, Robert S. Pickart, Fiammetta Straneo, Igor Yashayaev",
            "contributor_role": "data design, collection and/or processing",
            "publisher_name": "M. Susan Lozier; Yao Fu",
            "publisher_email": "susan.lozier@gatech.edu; yaofu@usf.edu",
        }

        # Process through the three-phase logic
        result = _consolidate_contributors(raw_attrs.copy())

        print("\nOSNAP Processing Result:")
        for key, value in result.items():
            if key.startswith("contributor_"):
                print(f"{key}: {repr(value)}")

        # The emails should be properly aligned with names
        # Extract the names and emails to check alignment
        names = result.get("contributor_name", "").split(", ")
        emails = result.get("contributor_email", "").split(", ")

        print(f"\nNames count: {len(names)}")
        print(f"Emails count: {len(emails)}")
        print(f"Names: {names[:5]}...")  # First 5 names
        print(f"Emails: {emails[:5]}...")  # First 5 emails

        # Check that M. Susan Lozier and Yao Fu (from publisher fields) have their emails
        # They should appear somewhere in the contributor list with their emails
        susan_lozier_idx = None
        yao_fu_idx = None

        for i, name in enumerate(names):
            if "Susan Lozier" in name:
                susan_lozier_idx = i
            if "Yao Fu" in name:
                yao_fu_idx = i

        print(f"\nSusan Lozier found at index: {susan_lozier_idx}")
        print(f"Yao Fu found at index: {yao_fu_idx}")

        if susan_lozier_idx is not None and susan_lozier_idx < len(emails):
            print(f"Susan Lozier's email: {emails[susan_lozier_idx]}")
            # Should be susan.lozier@gatech.edu

        if yao_fu_idx is not None and yao_fu_idx < len(emails):
            print(f"Yao Fu's email: {emails[yao_fu_idx]}")
            # Should be yaofu@usf.edu


class TestEmailValidation:
    """Test email address validation helper function."""

    def test_valid_emails(self):
        """Test that valid email addresses pass validation."""
        valid_emails = [
            "user@example.com",
            "test.email@domain.org",
            "name_with_underscore@test.edu",
            "user-name@example-domain.co.uk",
            "simple@test.io",
            "numbers123@domain456.net",
            "ben.moat@noc.ac.uk",
            "susan.lozier@gatech.edu",
            "yaofu@usf.edu",
        ]

        for email in valid_emails:
            assert contributors.is_valid_email(email), f"Should be valid: {email}"

    def test_invalid_emails(self):
        """Test that invalid email addresses fail validation."""
        invalid_emails = [
            "",  # Empty string
            "   ",  # Whitespace only
            "invalid.email",  # No @ symbol
            "@domain.com",  # No local part
            "user@",  # No domain
            "user@domain",  # No TLD
            "user@.com",  # Missing domain name
            "user name@domain.com",  # Space in local part
            "user@domain.c",  # TLD too short
            "user@@domain.com",  # Double @
            "user@domain@com",  # Multiple @ symbols
        ]

        for email in invalid_emails:
            assert not contributors.is_valid_email(email), f"Should be invalid: {email}"

    def test_email_validation_in_processing(self):
        """Test that email validation warnings are logged during processing."""
        # Create contributors with mix of valid and invalid emails
        contributors_dict = {
            "1": {
                "name": "Valid User",
                "email": "valid@example.com",
                "id": "",
                "role": "creator",
            },
            "2": {
                "name": "Invalid User",
                "email": "invalid.email",
                "id": "",
                "role": "PI",
            },
            "3": {"name": "Empty Email", "email": "", "id": "", "role": "contributor"},
        }

        # Process through enrichment (which includes email validation)
        result = contributors.enrich_contributors(contributors_dict)

        # Should return all contributors (validation doesn't reject, just warns)
        assert len(result) == 3
        assert result["1"]["email"] == "valid@example.com"
        assert result["2"]["email"] == "invalid.email"  # Invalid email preserved
        assert result["3"]["email"] == ""  # Empty email preserved


class TestSplitCleanFunction:
    """Test the shared _split_clean helper function used for both contributors and institutions."""

    def test_comma_separated_values(self):
        """Test basic comma separation."""
        result = contributors._split_clean("A, B, C")
        assert result == ["A", "B", "C"]

    def test_semicolon_separated_values(self):
        """Test basic semicolon separation."""
        result = contributors._split_clean("A; B; C")
        assert result == ["A", "B", "C"]

    def test_mixed_delimiters(self):
        """Test mixed comma and semicolon delimiters."""
        result = contributors._split_clean("A, B; C")
        assert result == ["A", "B", "C"]

        result = contributors._split_clean("A; B, C; D")
        assert result == ["A", "B", "C", "D"]

    def test_empty_values_preserved(self):
        """Test that empty values are preserved for alignment."""
        result = contributors._split_clean("A, , C")
        assert result == ["A", "", "C"]

        result = contributors._split_clean("A; ; C")
        assert result == ["A", "", "C"]

    def test_whitespace_handling(self):
        """Test proper whitespace trimming."""
        result = contributors._split_clean("  A  ,  B  ;  C  ")
        assert result == ["A", "B", "C"]

    def test_empty_string_input(self):
        """Test handling of empty/whitespace input."""
        assert contributors._split_clean("") == []
        assert contributors._split_clean("   ") == []

    def test_complex_real_world_example(self):
        """Test with complex real-world contributor data."""
        # Similar to NOAC47N case
        input_str = "Simon Wett, Monika Rhein, Dagmar Kieke, Christian Mertens, Martin Moritz; Hannah Nowitzki"
        result = contributors._split_clean(input_str)
        expected = [
            "Simon Wett",
            "Monika Rhein",
            "Dagmar Kieke",
            "Christian Mertens",
            "Martin Moritz",
            "Hannah Nowitzki",
        ]
        assert result == expected

    def test_institution_example(self):
        """Test with institution-style semicolon separation."""
        # Similar to OSNAP institutions
        input_str = "Georgia Institute of Technology; National Oceanography Centre (Southampton); Woods Hole Oceanographic Institution"
        result = contributors._split_clean(input_str)
        expected = [
            "Georgia Institute of Technology",
            "National Oceanography Centre (Southampton)",
            "Woods Hole Oceanographic Institution",
        ]
        assert result == expected

    def test_deduplication_function(self):
        """Test the _deduplicate_structured_dict function directly."""
        from amocatlas.contributors import _deduplicate_structured_dict

        # Test data with exact duplicates
        test_data = {
            "1": {
                "name": "John Doe",
                "role": "creator",
                "email": "john@ex.com",
                "id": "123",
            },
            "2": {
                "name": "John Doe",
                "role": "creator",
                "email": "john@ex.com",
                "id": "123",
            },  # Exact duplicate
            "3": {
                "name": "Jane Smith",
                "role": "PI",
                "email": "jane@ex.com",
                "id": "456",
            },
            "4": {
                "name": "John Doe",
                "role": "PI",
                "email": "john@ex.com",
                "id": "123",
            },  # Different role, not duplicate
        }

        result = _deduplicate_structured_dict(test_data)

        # Should have 3 entries (removed exact duplicate of entry 1)
        assert len(result) == 3
        assert result["1"]["name"] == "John Doe"
        assert result["1"]["role"] == "creator"
        assert result["2"]["name"] == "Jane Smith"  # Jane moved to position 2
        assert result["3"]["name"] == "John Doe"
        assert result["3"]["role"] == "PI"  # John with PI role kept

    def test_institutional_creator_overwrite(self):
        """Test that _overwrite fields replace institutional creators with individual contributors."""
        # Simulate Arctic Gateway case where original NetCDF has institutional creators
        # but YAML provides individual contributors via _overwrite fields
        raw_attrs = {
            # Original institutional creators/publishers (from NetCDF)
            "creator_name": "Norwegian Polar Institute (NPI)",
            "creator_email": "post@npolar.no",
            "creator_url": "www.npolar.no",
            "creator_type": "institution",
            "publisher_name": "Norwegian Polar Institute (NPI)",
            "publisher_email": "post@npolar.no",
            "publisher_url": "www.npolar.no",
            "publisher_type": "institution",
            # YAML overrides with individual contributors
            "creator_name_overwrite": "H. Fredriksen",
            "creator_url_overwrite": " ",  # Empty overwrite
            "creator_email_overwrite": " ",  # Empty overwrite
            "creator_type_overwrite": " ",  # Empty overwrite
            "publisher_name_overwrite": "H. Fredriksen",
            "publisher_email_overwrite": " ",  # Empty overwrite
            # Additional individual contributors
            "contributor_name": "H. Fredriksen, L. de Steur, W. von Appen, R. Ingvaldsen, R. McPherson, C. Lee, J. Lenetsky, R. Woodgate",
            "contributor_role": "creator, PI",
            "contributor_id": "https://orcid.org/0000-0002-3598-4076, https://orcid.org/0000-0002-6043-7920, https://orcid.org/0000-0002-7200-0099, https://orcid.org/0000-0002-8261-334X, https://orcid.org/0000-0002-4449-6701, https://orcid.org/0000-0002-3479-801X, https://orcid.org/0000-0003-1074-2764, https://psc.apl.uw.edu/people/investigators/rebecca-woodgate/",
        }

        # Apply overwrite logic manually (simulating what standardise_data does)
        test_attrs = raw_attrs.copy()

        # Apply overwrites (this is what happens in standardise_data before _consolidate_contributors)
        overwrite_applied = {}
        for key, value in test_attrs.items():
            if key.endswith("_overwrite"):
                # Extract the base key name (remove _overwrite suffix)
                base_key = key[:-10]  # Remove "_overwrite" (10 characters)
                # Apply overwrite
                test_attrs[base_key] = value
                overwrite_applied[base_key] = value

        from amocatlas.standardise import _consolidate_contributors

        result = _consolidate_contributors(test_attrs)

        print("\nInstitutional Creator Overwrite Test Result:")
        print(f"contributor_name: {repr(result.get('contributor_name', ''))}")

        # The result should NOT contain "Norwegian Polar Institute (NPI)"
        contributor_names = result.get("contributor_name", "")
        assert "Norwegian Polar Institute" not in contributor_names, (
            f"Institution should not appear in contributors: {contributor_names}"
        )
        assert "NPI" not in contributor_names, (
            f"Institution abbreviation should not appear in contributors: {contributor_names}"
        )

        # Should contain the individual contributors (registry enriches names)
        assert "Hege-Beate Fredriksen" in contributor_names  # H. Fredriksen enriched
        assert "Laura de Steur" in contributor_names  # L. de Steur enriched
        assert "Rebecca Woodgate" in contributor_names  # R. Woodgate enriched

        # The overwrite should replace institutional creator with individual
        # Hege-Beate Fredriksen should appear twice (creator + publisher roles are different)
        names_list = contributor_names.split(", ")
        frederiksen_count = sum(1 for name in names_list if "Fredriksen" in name)

        print(
            f"Hege-Beate Fredriksen appears {frederiksen_count} times in contributor list"
        )
        # Should appear twice: once as creator, once as publisher (different roles, not duplicates)
        assert frederiksen_count == 2, (
            f"Expected 2 instances of Fredriksen (different roles), got {frederiksen_count}"
        )


if __name__ == "__main__":
    pytest.main([__file__])
