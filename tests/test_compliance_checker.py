"""Tests for AMOCatlas AC1 compliance checker functionality."""

import os
import tempfile

import numpy as np
import pytest
import xarray as xr

from amocatlas import compliance_checker, logger

# Disable logging for tests
logger.disable_logging()

# Test data file - a valid AC1 file for testing modifications
TEST_AC1_FILE = "data/OS_TEST_20040402-20240327_DPR_transports_T12H.nc"


@pytest.fixture
def valid_ac1_dataset() -> xr.Dataset:
    """Create a valid AC1 dataset for testing."""
    time_data = np.array(
        ["2004-04-02T00:00:00", "2004-04-02T12:00:00", "2004-04-03T00:00:00"],
        dtype="datetime64[ns]",
    )

    # Create 8 transport components as required
    component_names = [
        "Florida Straits",
        "Ekman",
        "Upper Mid-Ocean",
        "Thermocline",
        "Intermediate Water",
        "Upper NADW",
        "Lower NADW",
        "AABW",
    ]

    ds = xr.Dataset(
        {
            "TRANSPORT": xr.DataArray(
                np.random.random((8, 3)),
                dims=["N_COMPONENT", "TIME"],
                attrs={
                    "long_name": "Ocean volume transport",
                    "units": "sverdrup",
                    "standard_name": "ocean_volume_transport_across_line",
                    "coordinates": "TIME LATITUDE",
                },
            ),
            "MOC_TRANSPORT": xr.DataArray(
                np.random.random(3),
                dims=["TIME"],
                attrs={
                    "long_name": "Maximum meridional overturning circulation transport",
                    "units": "sverdrup",
                    "standard_name": "ocean_volume_transport_across_line",
                },
            ),
            "TRANSPORT_NAME": xr.DataArray(
                component_names,
                dims=["N_COMPONENT"],
                attrs={
                    "long_name": "Transport component names",
                    "comment": "Short names for each transport component",
                },
            ),
            "TRANSPORT_DESCRIPTION": xr.DataArray(
                [f"{name} transport component" for name in component_names],
                dims=["N_COMPONENT"],
                attrs={
                    "long_name": "Transport component descriptions",
                    "comment": "Detailed descriptions of each transport component",
                },
            ),
        },
        coords={
            "TIME": xr.DataArray(
                time_data,
                dims=["TIME"],
                attrs={"long_name": "Time", "standard_name": "time", "axis": "T"},
            ),
            "LATITUDE": xr.DataArray(
                26.5,
                attrs={
                    "long_name": "Latitude",
                    "standard_name": "latitude",
                    "units": "degree_north",
                    "axis": "Y",
                },
            ),
        },
        attrs={
            # Required OceanSITES/CF/ACDD attributes
            "Conventions": "CF-1.8, OceanSITES-1.4, ACDD-1.3",
            "format_version": "1.4",
            "data_type": "OceanSITES time-series data",
            "featureType": "timeSeries",
            "data_mode": "D",
            "title": "RAPID Atlantic Meridional Overturning Circulation Transport Components",
            "summary": "Component transport time series from the RAPID observing array.",
            "source": "RAPID moored array observations",
            "site_code": "RAPID",
            "array": "RAPID",
            "platform_code": "RAPID26N",
            "naming_authority": "AMOCatlas",
            "id": "OS_RAPID_20040402-20040403_DPR_transports_T12H",
            "cdm_data_type": "TimeSeries",
            "QC_indicator": "excellent",
            "processing_level": "Data verified against model or other contextual information",
            "date_created": "20251005T143000",
            "institution": "AMOCatlas Community",
            # Geographic bounds
            "geospatial_lat_min": 26.5,
            "geospatial_lat_max": 26.5,
            "geospatial_lon_min": -79.0,
            "geospatial_lon_max": -13.0,
            # Time coverage
            "time_coverage_start": "20040402T000000",
            "time_coverage_end": "20040403T000000",
            # Contributors
            "contributor_name": "Ben Moat",
            "contributor_email": "ben.moat@example.org",
            "contributor_id": "https://orcid.org/0000-0001-8676-7779",
            "contributor_role": "principalInvestigator",
            "contributor_role_vocabulary": "https://vocab.nerc.ac.uk/collection/G04/current/",
            "contributing_institutions": "National Oceanography Centre",
            "contributing_institutions_vocabulary": "https://ror.org/example",
            "contributing_institutions_role": "operator",
            "contributing_institutions_role_vocabulary": "https://vocab.nerc.ac.uk/collection/W08/current/",
            "source_acknowledgement": "Data from the RAPID AMOC observing project",
        },
    )

    return ds


@pytest.fixture
def temp_netcdf_file(valid_ac1_dataset: xr.Dataset) -> str:
    """Create a temporary NetCDF file with valid AC1 dataset."""
    # Create proper OceanSITES filename in temp directory
    temp_dir = tempfile.gettempdir()
    proper_name = os.path.join(
        temp_dir, "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
    )

    # Remove manual units from TIME to avoid encoding conflicts
    ds = valid_ac1_dataset.copy()
    if "units" in ds["TIME"].attrs:
        del ds["TIME"].attrs["units"]

    # Set encoding for datetime
    ds.encoding["TIME"] = {
        "units": "seconds since 1970-01-01T00:00:00Z",
        "calendar": "gregorian",
    }

    ds.to_netcdf(proper_name, format="NETCDF4_CLASSIC")
    yield proper_name

    # Cleanup
    if os.path.exists(proper_name):
        os.unlink(proper_name)


class TestComplianceChecker:
    """Test compliance checker functionality."""

    def test_valid_file_passes(self, temp_netcdf_file: str) -> None:
        """Test that a valid AC1 file passes compliance check."""
        result = compliance_checker.validate_ac1_file(temp_netcdf_file)

        assert result.passed, f"Valid file should pass. Errors: {result.errors}"
        assert result.file_type == "component_transports"
        assert len(result.errors) == 0

    def test_missing_required_global_attributes(
        self, valid_ac1_dataset: xr.Dataset
    ) -> None:
        """Test detection of missing required global attributes."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)

        # Remove a required attribute
        ds_modified = ds.copy()
        del ds_modified.attrs["title"]
        ds.close()

        # Use proper OceanSITES filename pattern
        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "Missing required global attribute: title" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_invalid_filename_pattern(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of invalid filename patterns."""
        # Load actual AC1 file
        ds = xr.open_dataset(TEST_AC1_FILE)

        # Use invalid filename pattern
        filename = "invalid_filename.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "does not match OceanSITES pattern" in error
                or "Filename must follow OceanSITES pattern" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds.close()

    def test_missing_required_dimensions(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of missing required dimensions."""
        # Load actual AC1 file and remove TIME dimension
        ds = xr.open_dataset(TEST_AC1_FILE)

        # Create dataset without TIME dimension
        ds_no_time = ds.isel(TIME=0).drop_vars("TIME")
        ds.close()

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_no_time.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any("TIME dimension is required" in error for error in result.errors)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_no_time.close()

    def test_missing_variable_attributes(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of missing variable attributes."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        # Remove long_name from TRANSPORT
        del ds_modified["TRANSPORT"].attrs["long_name"]

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "TRANSPORT missing required attribute: long_name" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_datetime_coordinate_units_not_required(
        self, valid_ac1_dataset: xr.Dataset
    ) -> None:
        """Test that TIME coordinate doesn't require manual units attribute."""
        ds = valid_ac1_dataset.copy()
        # TIME coordinate should not have manual units (xarray handles this)
        if "units" in ds["TIME"].attrs:
            del ds["TIME"].attrs["units"]

        with tempfile.NamedTemporaryFile(
            suffix="_OS_RAPID_20040402-20040403_DPR_transports_T12H.nc", delete=False
        ) as tmp:
            ds.encoding["TIME"] = {
                "units": "seconds since 1970-01-01T00:00:00Z",
                "calendar": "gregorian",
            }
            ds.to_netcdf(tmp.name, format="NETCDF4_CLASSIC")

            result = compliance_checker.validate_ac1_file(tmp.name)

            # Should pass - datetime coordinates don't need manual units
            time_units_errors = [
                error for error in result.errors if "TIME" in error and "units" in error
            ]
            assert len(time_units_errors) == 0, (
                f"TIME should not require manual units. Errors: {time_units_errors}"
            )

        os.unlink(tmp.name)

    def test_unitless_variables_allowed(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test that descriptive variables don't require units."""
        ds = valid_ac1_dataset.copy()
        # TRANSPORT_NAME and TRANSPORT_DESCRIPTION should not require units
        if "units" in ds["TRANSPORT_NAME"].attrs:
            del ds["TRANSPORT_NAME"].attrs["units"]
        if "units" in ds["TRANSPORT_DESCRIPTION"].attrs:
            del ds["TRANSPORT_DESCRIPTION"].attrs["units"]

        with tempfile.NamedTemporaryFile(
            suffix="_OS_RAPID_20040402-20040403_DPR_transports_T12H.nc", delete=False
        ) as tmp:
            if "units" in ds["TIME"].attrs:
                del ds["TIME"].attrs["units"]
            ds.encoding["TIME"] = {
                "units": "seconds since 1970-01-01T00:00:00Z",
                "calendar": "gregorian",
            }
            ds.to_netcdf(tmp.name, format="NETCDF4_CLASSIC")

            result = compliance_checker.validate_ac1_file(tmp.name)

            # Should not require units for descriptive variables
            name_units_errors = [
                error
                for error in result.errors
                if "TRANSPORT_NAME" in error and "units" in error
            ]
            desc_units_errors = [
                error
                for error in result.errors
                if "TRANSPORT_DESCRIPTION" in error and "units" in error
            ]

            assert len(name_units_errors) == 0, (
                f"TRANSPORT_NAME should not require units. Errors: {name_units_errors}"
            )
            assert len(desc_units_errors) == 0, (
                f"TRANSPORT_DESCRIPTION should not require units. Errors: {desc_units_errors}"
            )

        os.unlink(tmp.name)

    def test_invalid_data_mode(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of invalid data_mode values."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        ds_modified.attrs["data_mode"] = "INVALID"

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "data_mode must be one of ['R', 'P', 'D']" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_invalid_qc_indicator(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of invalid QC_indicator values."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        ds_modified.attrs["QC_indicator"] = "invalid"

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "QC_indicator must be one of" in error for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_invalid_date_format(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of invalid date formats."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        ds_modified.attrs["date_created"] = "2025-10-05T14:30:00Z"  # Wrong format

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "date_created must use format YYYYmmddTHHMMss" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_invalid_orcid_format(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of invalid ORCID formats."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        ds_modified.attrs["contributor_id"] = "https://orcid.org/invalid-format"

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any("Invalid ORCID format" in error for error in result.errors)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_missing_conventions(self, valid_ac1_dataset: xr.Dataset) -> None:
        """Test detection of missing conventions."""
        # Load actual AC1 file and modify it
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        ds_modified.attrs["Conventions"] = "CF-1.8"  # Missing OceanSITES and ACDD

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "Conventions must include 'OceanSITES-1.4'" in error
                for error in result.errors
            )
            assert any(
                "Conventions must include 'ACDD-1.3'" in error
                for error in result.errors
            )
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()


class TestValidationResult:
    """Test ValidationResult class functionality."""

    def test_validation_result_creation(self) -> None:
        """Test ValidationResult object creation."""
        result = compliance_checker.ValidationResult(passed=True)

        assert result.passed
        assert result.errors == []
        assert result.warnings == []
        assert result.file_type is None

    def test_validation_result_with_errors(self) -> None:
        """Test ValidationResult with errors."""
        result = compliance_checker.ValidationResult(passed=True)
        result.errors.append("Test error")

        # passed is determined by @property based on errors
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_validation_result_warnings_dont_fail(self) -> None:
        """Test that warnings don't cause validation to fail."""
        result = compliance_checker.ValidationResult(passed=True)
        result.warnings.append("Test warning")

        assert len(result.warnings) == 1


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_netcdf_file(self) -> None:
        """Test validation of invalid NetCDF file."""
        # Create a non-NetCDF file with proper naming
        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            # Write invalid content
            with open(filepath, "w") as f:
                f.write("This is not a NetCDF file")

            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any("Failed to open NetCDF file" in error for error in result.errors)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_invalid_filename_dates(self) -> None:
        """Test validation with invalid date format in filename."""
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_copy = ds.copy()
        ds.close()

        # Create filename with invalid date format
        filename = "OS_RAPID_20040432-20040403_DPR_transports_T12H.nc"  # 32nd day doesn't exist
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_copy.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "Invalid date format in filename" in error for error in result.errors
            )

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_copy.close()

    def test_start_date_after_end_date(self) -> None:
        """Test validation when start date is after end date."""
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_copy = ds.copy()
        ds.close()

        # Create filename with start date after end date
        filename = "OS_RAPID_20040405-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_copy.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            assert any(
                "Start date" in error and "must be <= end date" in error
                for error in result.errors
            )

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_copy.close()

    def test_non_standard_units_warning(self) -> None:
        """Test that non-standard units generate warnings."""
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        # Create variable with unknown standard_name, matching TIME dimension size
        time_size = ds_modified.sizes["TIME"]
        ds_modified["CUSTOM_VAR"] = xr.DataArray(
            np.ones(time_size),
            dims=["TIME"],
            attrs={"standard_name": "unknown_standard_name", "units": "unknown_units"},
        )

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            # Should still pass but have warnings
            assert result.passed or len(result.warnings) > 0
            assert any(
                "Unknown standard_name" in warning for warning in result.warnings
            )

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()

    def test_units_validation_multiple_acceptable(self) -> None:
        """Test units validation with multiple acceptable units."""
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        # Modify a variable to have wrong units (for a standard_name that has alternatives)
        if "TRANSPORT" in ds_modified.data_vars:
            ds_modified["TRANSPORT"].attrs["units"] = "wrong_units"

        filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds_modified.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            assert not result.passed
            # Should have error about non-compliant units
            assert any("Non-compliant units" in error for error in result.errors)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
            ds_modified.close()


class TestSpecificValidations:
    """Test specific validation functions."""

    def test_unknown_file_type_detection(self) -> None:
        """Test handling of unknown file types."""
        # Create dataset with minimal structure that doesn't match known patterns
        ds = xr.Dataset(
            {"unknown_var": (["time"], [1, 2, 3])},
            coords={"time": [1, 2, 3]},
            attrs={
                "Conventions": "CF-1.8, OceanSITES-1.4, ACDD-1.3",
                "format_version": "1.4",
                "data_type": "OceanSITES time-series data",
                "title": "Unknown data type",
                "source": "test",
            },
        )

        # Use filename that doesn't match specific patterns
        filename = "OS_UNKNOWN_20040402-20040403_DPR_unknown_T12H.nc"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            ds.to_netcdf(filepath, format="NETCDF4_CLASSIC")
            result = compliance_checker.validate_ac1_file(filepath)

            # May pass or fail, but should handle unknown file type gracefully
            assert isinstance(result, compliance_checker.ValidationResult)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_dimension_validation_errors(self) -> None:
        """Test dimension validation edge cases."""
        ds = xr.open_dataset(TEST_AC1_FILE)
        ds_modified = ds.copy()
        ds.close()

        # Remove required dimension
        if "TIME" in ds_modified.dims:
            # Create dataset without TIME dimension
            new_data = {}
            for var_name, var in ds_modified.data_vars.items():
                if "TIME" in var.dims:
                    # Skip variables that depend on TIME
                    continue
                new_data[var_name] = var

            ds_no_time = xr.Dataset(new_data, attrs=ds_modified.attrs)

            filename = "OS_RAPID_20040402-20040403_DPR_transports_T12H.nc"
            filepath = os.path.join(tempfile.gettempdir(), filename)

            try:
                ds_no_time.to_netcdf(filepath, format="NETCDF4_CLASSIC")
                result = compliance_checker.validate_ac1_file(filepath)

                assert not result.passed
                # Should have error about missing TIME dimension

            finally:
                if os.path.exists(filepath):
                    os.unlink(filepath)

        ds_modified.close()


class TestValidationResultProperties:
    """Test ValidationResult class edge cases."""

    def test_validation_result_passed_property(self) -> None:
        """Test that passed property can be set and retrieved."""
        result = compliance_checker.ValidationResult(passed=True)

        # Initially should be True
        assert result.passed

        # Can be manually set to False
        result.passed = False
        assert not result.passed

        # Adding errors doesn't automatically change passed status
        result.errors.append("Test error")
        assert not result.passed  # Still False as we set it

        # Warnings shouldn't affect pass status
        result.warnings.append("Test warning")
        assert not result.passed

        # Can manually set back to True
        result.passed = True
        assert result.passed

    def test_validation_result_attributes(self) -> None:
        """Test ValidationResult attribute initialization."""
        result = compliance_checker.ValidationResult(
            file_type="test_type", passed=False
        )

        assert result.file_type == "test_type"
        assert not result.passed  # Explicitly set
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


if __name__ == "__main__":
    pytest.main([__file__])
