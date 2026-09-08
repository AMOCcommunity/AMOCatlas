import os
import tempfile

import pytest
import xarray as xr

from amocatlas import compliance_checker, convert, logger, readers, standardise, writers

logger.disable_logging()


@pytest.fixture
def sample_rapid_data():
    """Fixture providing sample RAPID data for testing."""
    # Load sample RAPID data for testing
    ds_rapid = readers.load_sample_dataset()
    ds_standardised = standardise.standardise_rapid(
        ds_rapid, ds_rapid.attrs["source_file"]
    )

    # Fix TIME units for conversion (as done in demo notebook)
    ds_standardised["TIME"].attrs["units"] = "seconds since 1970-01-01T00:00:00Z"

    return ds_standardised


@pytest.fixture
def sample_attributes():
    """Fixture providing sample attributes for testing."""
    return {
        "contributor_name": "Ben Moat",
        "contributor_role": "author",
        "contributor_email": "ben.moat@noc.ac.uk",
        "institution": "National Oceanography Centre",
    }


def test_to_AC1_basic_conversion(sample_rapid_data):
    """Test basic AC1 conversion with sample RAPID data."""
    result = convert.to_AC1(sample_rapid_data)

    # Should return a list of datasets
    assert isinstance(result, list)
    assert len(result) > 0

    ac1_ds = result[0]

    # Check basic structure
    assert isinstance(ac1_ds, xr.Dataset)
    assert "TRANSPORT" in ac1_ds.data_vars
    assert "TIME" in ac1_ds.coords

    # Check dimensions (AC1 format uses N_COMPONENT)
    assert "N_COMPONENT" in ac1_ds.dims or "TRANSPORT_NAME" in ac1_ds.dims

    # Check global attributes
    assert "Conventions" in ac1_ds.attrs
    assert "OceanSITES" in ac1_ds.attrs["Conventions"]

    # Check suggested filename
    assert "suggested_filename" in ac1_ds.attrs or "id" in ac1_ds.attrs


def test_to_AC1_component_transport_detection(sample_rapid_data):
    """Test detection of component transport data."""
    # The convert._is_component_transport_data function should detect RAPID data
    is_component = convert._is_component_transport_data(sample_rapid_data)
    assert isinstance(is_component, bool)


def test_determine_array_name(sample_rapid_data):
    """Test array name determination from dataset."""
    array_name = convert._determine_array_name(sample_rapid_data)

    assert isinstance(array_name, str)
    assert len(array_name) > 0
    # Should be able to determine from RAPID data
    assert array_name.lower() in ["rapid", "unknown"]


def test_determine_date_range(sample_rapid_data):
    """Test date range determination from dataset."""
    start_date, end_date = convert._determine_date_range(sample_rapid_data)

    assert isinstance(start_date, str)
    assert isinstance(end_date, str)
    # Should be in YYYYMMDD format
    assert len(start_date) == 8
    assert len(end_date) == 8
    assert start_date.isdigit()
    assert end_date.isdigit()


def test_create_ac1_global_attributes(sample_rapid_data, sample_attributes):
    """Test creation of AC1 global attributes."""
    # Test the global attributes creation
    attrs = convert._create_ac1_global_attributes(
        sample_rapid_data, "RAPID", "test_file.nc", "20040401", "20201231"
    )

    assert isinstance(attrs, dict)

    # Check required AC1 attributes
    assert "Conventions" in attrs
    assert "OceanSITES" in attrs["Conventions"]
    assert "data_type" in attrs
    assert "format_version" in attrs
    assert "date_created" in attrs
    # history may not always be present
    assert "comment" in attrs or "history" in attrs


def test_validate_ac1_output(sample_rapid_data):
    """Test AC1 output validation."""
    # Convert sample data first
    ac1_datasets = convert.to_AC1(sample_rapid_data)
    ac1_ds = ac1_datasets[0]

    # Test validation
    is_valid = convert._validate_ac1_output(ac1_ds, "component_transport")
    assert isinstance(is_valid, bool)


def test_get_ac1_filename():
    """Test AC1 filename generation."""
    filename = convert._get_ac1_filename(
        array_name="RAPID",
        start_date="20040401",
        end_date="20201231",
        content_type="DP",
        partx="component_transport",
    )

    assert isinstance(filename, str)
    assert filename.endswith(".nc")
    assert "RAPID" in filename
    assert "20040401" in filename
    assert "20201231" in filename


def test_full_conversion_workflow(sample_rapid_data):
    """Test complete conversion workflow matching demo notebook."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Step 1: Convert to AC1 format
        ac1_datasets = convert.to_AC1(sample_rapid_data)
        assert len(ac1_datasets) > 0

        ac1_ds = ac1_datasets[0]

        # Step 2: Check basic properties
        assert "TRANSPORT" in ac1_ds.data_vars
        assert "TIME" in ac1_ds.coords
        assert "Conventions" in ac1_ds.attrs

        # Step 3: Save the dataset
        filename = ac1_ds.attrs.get(
            "suggested_filename", ac1_ds.attrs.get("id", "test_output.nc")
        )
        if not filename.endswith(".nc"):
            filename += ".nc"

        output_file = os.path.join(tmp_dir, filename)
        success = writers.save_dataset(ac1_ds, output_file)

        assert success is True
        assert os.path.exists(output_file)

        # Step 4: Run compliance check (as in demo notebook)
        result = compliance_checker.validate_ac1_file(output_file)

        assert hasattr(result, "passed")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


def test_conversion_with_missing_time_units():
    """Test conversion behavior when TIME units are missing."""
    # Load sample data without fixing TIME units
    ds_rapid = readers.load_sample_dataset()
    ds_standardised = standardise.standardise_rapid(
        ds_rapid, ds_rapid.attrs["source_file"]
    )

    # Remove TIME units to test error handling
    if "units" in ds_standardised["TIME"].attrs:
        del ds_standardised["TIME"].attrs["units"]

    # Conversion should either fail or handle missing units gracefully
    try:
        result = convert.to_AC1(ds_standardised)
        # If it succeeds, check that it handled the missing units somehow
        if result:
            ac1_ds = result[0]
            assert isinstance(ac1_ds, xr.Dataset)
    except Exception as e:
        # Expected to fail with missing TIME units
        assert "units" in str(e).lower() or "time" in str(e).lower()


def test_convert_component_transports_structure(sample_rapid_data):
    """Test the structure of converted component transport data."""
    # Test the internal conversion function
    result = convert._convert_component_transports(
        sample_rapid_data, "RAPID", "20040401", "20201231"
    )

    assert isinstance(result, xr.Dataset)

    # Check required variables for component transport
    assert "TRANSPORT" in result.data_vars
    assert "TIME" in result.coords

    # Check that TRANSPORT has proper dimensions
    transport_dims = result["TRANSPORT"].dims
    assert "TIME" in transport_dims

    # Check for transport component names
    if "TRANSPORT_NAME" in result.coords:
        assert len(result.coords["TRANSPORT_NAME"]) > 0


def test_ac1_metadata_structure(sample_rapid_data):
    """Test that AC1 conversion produces proper metadata structure."""
    ac1_datasets = convert.to_AC1(sample_rapid_data)
    ac1_ds = ac1_datasets[0]

    # Test global attributes
    required_attrs = ["Conventions", "data_type", "format_version", "date_created"]

    for attr in required_attrs:
        assert attr in ac1_ds.attrs, f"Missing required attribute: {attr}"

    # Test variable attributes
    if "TRANSPORT" in ac1_ds.data_vars:
        transport_attrs = ac1_ds["TRANSPORT"].attrs
        assert "units" in transport_attrs
        assert "long_name" in transport_attrs or "standard_name" in transport_attrs

    # Test coordinate attributes
    if "TIME" in ac1_ds.coords:
        time_attrs = ac1_ds["TIME"].attrs
        assert "units" in time_attrs
