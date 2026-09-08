"""Tests for amocatlas.standardise module.

Tests the standardization pipeline including metadata application,
variable renaming, and dataset enrichment.
"""

import warnings

import pandas as pd
import pytest
import xarray as xr

from amocatlas import readers, standardise
from amocatlas.logger import disable_logging

# Disable logging for cleaner test output
disable_logging()


class TestStandardizeData:
    """Integration tests for data standardization."""

    @pytest.mark.slow
    def test_standardise_data_rapid(self):
        """Test end-to-end standardization of RAPID data."""
        # Load raw RAPID data
        raw_datasets = readers.load_dataset("rapid")
        raw_dataset = raw_datasets[0]  # Transport file

        # Standardize the data
        standardized = standardise.standardise_data(
            raw_dataset, file_name="moc_transports.nc"
        )

        # Should have AMOCatlas metadata
        assert "processing_datasource" in standardized.attrs
        assert standardized.attrs["processing_datasource"] == "rapid26n"

        # Should have applied variable mapping
        assert "applied_variable_mapping" in standardized.attrs
        mapping = standardized.attrs["applied_variable_mapping"]
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

        # Internal working structures must not leak into the output attrs
        # (they are nested dicts and not netCDF-serialisable).
        for internal in ("files", "variable_mapping", "original_variable_metadata"):
            assert internal not in standardized.attrs

        # Should have standardized variable names
        std_vars = list(standardized.data_vars)

        # MOC variable should be present and standardized
        assert "MOC" in std_vars

        # Time coordinate should be standardized
        assert "TIME" in standardized.coords

        # Should have processing metadata
        assert "date_modified" in standardized.attrs  # Changed from processing_date
        assert "processing_software" in standardized.attrs
        assert "processing_version" in standardized.attrs

        # Should preserve data values while changing names
        assert standardized.sizes["TIME"] == raw_dataset.sizes["time"]

    @pytest.mark.slow
    def test_standardise_data_with_real_metadata(self):
        """Test that read.rapid() produces properly standardized data."""
        # Test that the new read API produces standardized data
        from amocatlas import read

        result = (
            read.rapid()
        )  # Loads single moc_transports.nc file (1.11MB) - already standardized

        # Should have basic standardization applied
        assert "processing_datasource" in result.attrs
        assert "processing_software" in result.attrs
        assert result.attrs["processing_datasource"] == "rapid26n"

        # Should have standardized variable names
        assert "MOC" in result.data_vars
        assert "TIME" in result.coords


class TestMetadataFunctions:
    """Unit tests for metadata handling functions."""

    def test_reorder_metadata(self):
        """Test metadata reordering according to GLOBAL_ATTR_ORDER."""
        # Create metadata in wrong order
        metadata = {
            "comment": "A comment",
            "title": "Test Title",
            "Conventions": "CF-1.8",  # Case-sensitive
            "description": "Test description",
            "featureType": "timeSeries",  # Case-sensitive
            "random_attr": "Some value",
        }

        result = standardise.reorder_metadata(metadata)
        result_keys = list(result.keys())

        # Should preserve case-sensitive attributes exactly
        assert "Conventions" in result_keys
        assert "featureType" in result_keys

        # Should follow GLOBAL_ATTR_ORDER for known attributes
        title_idx = result_keys.index("title")
        desc_idx = result_keys.index("description")
        assert title_idx < desc_idx  # Title comes before description

        # Unknown attributes should be at the end
        assert result_keys.index("random_attr") > desc_idx

    def test_get_amocatlas_version(self):
        """Test version detection."""
        version = standardise.get_dynamic_version()

        # Should return a reasonable version string
        assert isinstance(version, str), (
            f"Version should be string, got {type(version)}: {repr(version)}"
        )
        assert len(version) > 0, f"Version should not be empty, got: {repr(version)}"

        # Should be in some recognizable format (digits OR hex chars for git commits)
        has_digits = any(char.isdigit() for char in version)
        has_hex_chars = any(char in "abcdef" for char in version.lower())
        assert has_digits or has_hex_chars, (
            f"Version should contain digits or hex characters, got: {repr(version)}"
        )

    def test_standardize_time_coordinate(self):
        """Test TIME coordinate standardization."""
        # Create test dataset with time coordinate
        ds = xr.Dataset(
            {"data": (["TIME"], [1, 2, 3])},
            coords={"time": pd.date_range("2020-01-01", periods=3)},
        )

        result = standardise.standardize_time_coordinate(ds)

        # Should have TIME coordinate
        assert "TIME" in result.coords

        # Should have standard attributes
        time_attrs = result["TIME"].attrs
        assert "standard_name" in time_attrs
        assert time_attrs["standard_name"] == "time"

    def test_clean_metadata(self):
        """Test metadata cleaning functionality."""
        # Test the clean_metadata function that exists
        metadata = {
            "Title": "Test Title",
            "TITLE": "Duplicate title",  # Duplicate should be resolved
            "creator_name": "Test Author",
            "principal_investigator": "Test PI",  # Should be consolidated with creator_name
            "Institution": "Test Institution",
            "Acknowledgement": "Test Acknowledgement",
        }

        result = standardise.clean_metadata(metadata)

        # Should return a cleaned dictionary
        assert isinstance(result, dict)
        assert len(result) > 0

        # Should consolidate contributor fields: creator_name should be removed and contributor_name added
        assert "creator_name" not in result  # Original field should be removed
        assert (
            "contributor_name" in result
        )  # Should be consolidated into standard contributor field

        # Should normalize acknowledgement spelling
        assert "acknowledgment" in result  # American spelling

        # Should resolve title duplicates (keeping one)
        title_count = sum(1 for k in result.keys() if k.lower().startswith("title"))
        assert title_count == 1  # Should have only one title field after deduplication


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.slow
    def test_standardise_data_edge_case(self):
        """Test standardization edge case with real rapid data."""
        # Use real rapid data since empty dataset needs metadata files
        from amocatlas import read

        rapid_data = read.rapid(raw=True)  # Raw data

        result = standardise.standardise_data(rapid_data, file_name="moc_transports.nc")

        # Should still have basic standardization
        assert "processing_datasource" in result.attrs
        assert isinstance(result, xr.Dataset)

    def test_reorder_metadata_empty(self):
        """Test metadata reordering with empty metadata."""
        result = standardise.reorder_metadata({})
        assert result == {}

    def test_reorder_metadata_case_sensitivity(self):
        """Test that case-sensitive attributes are preserved exactly."""
        metadata = {
            "conventions": "wrong case",  # lowercase
            "Conventions": "CF-1.8",  # correct case
            "featuretype": "wrong case",  # lowercase
            "featureType": "timeSeries",  # correct case
        }

        result = standardise.reorder_metadata(metadata)

        # Should preserve exact case for case-sensitive attributes
        assert result["Conventions"] == "CF-1.8"
        assert result["featureType"] == "timeSeries"

        # Should also preserve the lowercase versions (different attributes)
        assert result["conventions"] == "wrong case"
        assert result["featuretype"] == "wrong case"

    def test_version_fallback(self):
        """Test version detection fallback mechanisms."""
        # This tests that version detection doesn't crash
        # and provides some fallback even in edge cases

        import subprocess
        from unittest import mock

        with mock.patch("subprocess.run") as mock_run:
            # Mock git failure with the proper exception type that the function catches
            mock_run.side_effect = subprocess.SubprocessError("Git not found")

            version = standardise.get_dynamic_version()

            # Should still return something reasonable
            assert isinstance(version, str)
            assert len(version) > 0


class TestConflictResolution:
    """Field-typed metadata conflict resolution."""

    def test_wrong_hemisphere_latitude_keeps_source_and_warns(self):
        """A numeric mismatch keeps the source-of-truth value and warns, not longest."""
        with pytest.warns(UserWarning, match="Metadata conflict"):
            result = standardise.resolve_metadata_conflict(
                "geospatial_lat_min",
                "26.5",
                "-26.5",
                "original file",
                "array-level YAML",
            )
        # '-26.5' is the longer string but must NOT win for a numeric field.
        assert result == "26.5"

    def test_equivalent_numbers_do_not_warn(self):
        """Numerically equal values resolve silently."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = standardise.resolve_metadata_conflict(
                "geospatial_lat_min", "26.5", "26.50"
            )
        assert result == "26.5"
        assert not [w for w in caught if "Metadata conflict" in str(w.message)]

    def test_date_mismatch_keeps_source_and_warns(self):
        """A genuine date mismatch keeps existing and warns."""
        with pytest.warns(UserWarning, match="Metadata conflict"):
            result = standardise.resolve_metadata_conflict(
                "time_coverage_end", "2024-05-18", "2020-12-31"
            )
        assert result == "2024-05-18"

    def test_equivalent_dates_do_not_warn(self):
        """Dates that parse to the same instant resolve silently."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = standardise.resolve_metadata_conflict(
                "time_coverage_start", "2004-02-15", "2004-02-15T00:00:00"
            )
        assert result == "2004-02-15"
        assert not [w for w in caught if "Metadata conflict" in str(w.message)]

    def test_tz_aware_and_same_day_dates_do_not_warn(self):
        """A nominal day-precision YAML date agrees with the file's precise timestamp.

        Covers both a tz-aware/naive pair (same instant) and a same-day/different-time
        pair, which previously raised spurious 'date mismatch' warnings.
        """
        for existing, new in [
            ("1996-05-01T00:00:00Z", "1996-05-01"),  # tz-aware vs naive, same instant
            ("2021-08-07T17:00:00Z", "2021-08-07"),  # same calendar day, 17h apart
        ]:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = standardise.resolve_metadata_conflict(
                    "time_coverage_end", existing, new
                )
            assert result == existing
            assert not [w for w in caught if "Metadata conflict" in str(w.message)]

    def test_different_calendar_day_still_warns(self):
        """A genuine multi-day difference (nominal YAML wrong by days) still conflicts."""
        with pytest.warns(UserWarning, match="Metadata conflict"):
            result = standardise.resolve_metadata_conflict(
                "time_coverage_start", "2004-04-06T00:00:00Z", "2004-04-01"
            )
        assert result == "2004-04-06T00:00:00Z"

    def test_doi_mismatch_keeps_source_and_warns(self):
        """A differing identifier keeps existing and warns rather than using length."""
        with pytest.warns(UserWarning, match="Metadata conflict"):
            result = standardise.resolve_metadata_conflict(
                "doi", "10.5281/zenodo.1", "10.5281/zenodo.22222"
            )
        assert result == "10.5281/zenodo.1"

    def test_update_interval_not_misclassified_as_date(self):
        """A key containing the substring 'date' is not treated as a date field."""
        assert standardise._classify_conflict_field("update_interval") == "text"

    def test_free_text_uses_longer_value_without_warning(self):
        """Free text keeps the longer value and does not warn (avoids noise)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = standardise.resolve_metadata_conflict(
                "description", "short", "a considerably longer description"
            )
        assert result == "a considerably longer description"
        assert not [w for w in caught if "Metadata conflict" in str(w.message)]


class TestTimeCoverageDerivation:
    """time_coverage_start/end are derived from the TIME coordinate, not nominal attrs."""

    def test_derived_from_time_coordinate(self):
        """Start/end come from TIME min/max as ISO-8601 Z strings."""
        import numpy as np
        import xarray as xr

        ds = xr.Dataset(
            coords={
                "TIME": (
                    "TIME",
                    np.array(["2004-04-02", "2024-03-27"], dtype="datetime64[ns]"),
                )
            }
        )
        assert standardise._time_coverage_from_data(ds) == (
            "2004-04-02T00:00:00Z",
            "2024-03-27T00:00:00Z",
        )

    def test_nat_values_are_ignored(self):
        """NaT entries are dropped before taking min/max."""
        import numpy as np
        import xarray as xr

        ds = xr.Dataset(
            coords={
                "TIME": (
                    "TIME",
                    np.array(
                        ["2005-01-15", "NaT", "2021-08-07"], dtype="datetime64[ns]"
                    ),
                )
            }
        )
        assert standardise._time_coverage_from_data(ds) == (
            "2005-01-15T00:00:00Z",
            "2021-08-07T00:00:00Z",
        )

    def test_none_when_time_not_datetime(self):
        """A non-datetime TIME yields (None, None) so callers keep existing attrs."""
        import numpy as np
        import xarray as xr

        ds = xr.Dataset(coords={"TIME": ("TIME", np.array([1.0, 2.0]))})
        assert standardise._time_coverage_from_data(ds) == (None, None)


class TestTimeCoordinate:
    """TIME coordinate standardisation, including non-1970 epochs."""

    def test_parse_cf_time_units(self):
        """CF units strings parse into (pandas unit, origin); junk returns None.

        A trailing UTC "Z" is stripped from the origin, because pandas' to_datetime
        rejects a timezone-aware origin when a unit is given (values are UTC regardless).
        """
        assert standardise._parse_cf_time_units("days since 1950-01-01") == (
            "D",
            "1950-01-01",
        )
        assert standardise._parse_cf_time_units(
            "seconds since 1970-01-01T00:00:00Z"
        ) == ("s", "1970-01-01T00:00:00")
        assert standardise._parse_cf_time_units("hours since 2000-01-01") == (
            "h",
            "2000-01-01",
        )
        assert standardise._parse_cf_time_units("garbage") is None
        assert standardise._parse_cf_time_units("furlongs since 1900") is None

    def test_numeric_time_honours_declared_epoch(self):
        """A 'days since 1950-01-01' coordinate decodes to 1950, not 1970."""
        ds = xr.Dataset(coords={"TIME": ("TIME", [0.0, 1.0, 365.0])})
        ds["TIME"].attrs["units"] = "days since 1950-01-01"
        out = standardise.standardize_time_coordinate(ds)
        assert pd.Timestamp(out["TIME"].values[0]) == pd.Timestamp("1950-01-01")
        assert pd.Timestamp(out["TIME"].values[1]) == pd.Timestamp("1950-01-02")
        assert pd.Timestamp(out["TIME"].values[2]) == pd.Timestamp("1951-01-01")

    def test_unknown_units_warn_and_fall_back(self):
        """Unrecognised TIME units warn and fall back to seconds since 1970."""
        ds = xr.Dataset(coords={"TIME": ("TIME", [0.0, 1.0])})
        ds["TIME"].attrs["units"] = "weird units"
        with pytest.warns(UserWarning, match="not understood"):
            out = standardise.standardize_time_coordinate(ds)
        assert pd.Timestamp(out["TIME"].values[0]) == pd.Timestamp("1970-01-01")

    def test_output_units_is_udunits_not_dtype_name(self):
        """Standardised TIME reports a UDUNITS string, not the numpy dtype name."""
        ds = xr.Dataset(coords={"TIME": ("TIME", [0.0, 1.0])})
        ds["TIME"].attrs["units"] = "seconds since 1970-01-01"
        out = standardise.standardize_time_coordinate(ds)
        assert out["TIME"].attrs["units"] == "seconds since 1970-01-01T00:00:00Z"
        assert "datetime64" not in out["TIME"].attrs["units"]
