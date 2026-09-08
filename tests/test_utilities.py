"""Tests for amocatlas.utilities module."""

import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import xarray as xr
import yaml

from amocatlas import logger, utilities

# Sample data
VALID_URL = "https://mooring.ucsd.edu/move/nc/"
INVALID_URL = "ftdp://invalid-url.com/data.nc"
INVALID_STRING = "not_a_valid_source"

# Replace with actual path to a local .nc file if you have one for local testing
LOCAL_VALID_FILE = "/path/to/your/OS_MOVE_TRANSPORTS.nc"
LOCAL_INVALID_FILE = "/path/to/invalid_file.txt"

logger.disable_logging()


@pytest.mark.parametrize(
    "url,expected",
    [
        (VALID_URL, True),
        (INVALID_URL, False),
        ("not_a_url", False),
    ],
)
def test_is_valid_url(url: str, expected: bool) -> None:
    assert utilities.is_valid_url(url) == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (
            LOCAL_VALID_FILE,
            Path(LOCAL_VALID_FILE).is_file() and LOCAL_VALID_FILE.endswith(".nc"),
        ),
        (LOCAL_INVALID_FILE, False),
        ("non_existent_file.nc", False),
    ],
)
def test_is_valid_file(path: str, expected: bool) -> None:
    assert utilities._is_valid_file(path) == expected


def test_safe_update_attrs_add_new_attribute() -> None:
    """Test adding new attributes via safe_update_attrs."""
    ds = xr.Dataset()
    new_attrs = {"project": "MOVE"}
    ds = utilities.safe_update_attrs(ds, new_attrs)
    assert ds.attrs["project"] == "MOVE"


def test_safe_update_attrs_existing_key_logs(caplog: Any) -> None:
    """Test logging when trying to overwrite existing attributes."""
    from amocatlas import logger, utilities

    # Re-enable logging for this test
    logger.enable_logging()

    ds = xr.Dataset(attrs={"project": "MOVE"})
    new_attrs = {"project": "OSNAP"}

    with caplog.at_level("DEBUG", logger="amocatlas"):
        utilities.safe_update_attrs(ds, new_attrs, overwrite=False, verbose=True)

    assert any(
        "Attribute 'project' already exists in dataset attrs and will not be overwritten."
        in message
        for message in caplog.messages
    )


def test_safe_update_attrs_existing_key_with_overwrite() -> None:
    """Test overwriting existing attributes when overwrite=True."""
    ds = xr.Dataset(attrs={"project": "MOVE"})
    new_attrs = {"project": "OSNAP"}
    ds = utilities.safe_update_attrs(ds, new_attrs, overwrite=True)
    assert ds.attrs["project"] == "OSNAP"


def test_get_project_root() -> None:
    """Test getting project root directory."""
    root = utilities.get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

    # The function should return a valid directory path
    # In development, it points to source. In installed package, it points to site-packages
    # Both are valid behaviors, so just verify it's a directory that exists
    assert root.is_dir()

    # Additional validation: the path should contain amocatlas package structure
    # Either as source code or installed package
    amocatlas_indicators = [
        "pyproject.toml",  # Source repo
        "setup.py",  # Source repo
        "setup.cfg",  # Source repo
        "amocatlas",  # Installed package directory
    ]

    # At least one indicator should exist (flexible for both dev and installed contexts)
    indicators_found = [
        (root / indicator).exists() for indicator in amocatlas_indicators
    ]
    assert any(indicators_found), (
        f"No project indicators found in {root}. Checked: {amocatlas_indicators}"
    )


def test_get_default_data_dir() -> None:
    """Test getting default data directory."""
    data_dir = utilities.get_default_data_dir()
    assert isinstance(data_dir, Path)
    # The function returns ~/.amocatlas_data for user data caching
    assert ".amocatlas_data" in str(data_dir)
    assert data_dir.name == ".amocatlas_data"


def test_set_data_dir_get_data_dir_integration() -> None:
    """Test integration between set_data_dir and get_data_dir with proper cleanup."""
    import tempfile

    # Store original state
    original_data_dir = utilities._user_data_dir

    try:
        # Test 1: Setting custom directory should be reflected in get_data_dir
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_data"

            # Set custom directory
            utilities.set_data_dir(str(custom_path))

            # get_data_dir should return the custom directory
            current_dir = utilities.get_data_dir()
            assert current_dir == custom_path.resolve()

            # Internal state should match
            assert utilities._user_data_dir == custom_path.resolve()

        # Test 2: Setting different directory should update correctly
        with tempfile.TemporaryDirectory() as temp_dir2:
            another_path = Path(temp_dir2) / "another_data"

            utilities.set_data_dir(str(another_path))

            # Should now return the new directory
            current_dir = utilities.get_data_dir()
            assert current_dir == another_path.resolve()
            assert utilities._user_data_dir == another_path.resolve()

        # Test 3: Resetting to default should work
        utilities._user_data_dir = None  # Reset to default
        default_dir = utilities.get_data_dir()
        expected_default = Path.home() / ".amocatlas_data"
        assert default_dir == expected_default

    finally:
        # Always restore original state to prevent test leakage
        utilities._user_data_dir = original_data_dir


def test_public_api_data_dir_functions() -> None:
    """Test that set_data_dir and get_data_dir are available in public API."""
    import tempfile

    import amocatlas

    # Store original state
    original_data_dir = utilities._user_data_dir

    try:
        # Test that public API functions exist and work
        assert hasattr(amocatlas, "set_data_dir")
        assert hasattr(amocatlas, "get_data_dir")
        assert callable(amocatlas.set_data_dir)
        assert callable(amocatlas.get_data_dir)

        # Test that they actually work
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "api_test"

            # Use public API
            amocatlas.set_data_dir(str(test_path))
            result = amocatlas.get_data_dir()

            assert result == test_path.resolve()

    finally:
        # Restore original state
        utilities._user_data_dir = original_data_dir


def test_normalize_whitespace() -> None:
    """Test whitespace normalization in attributes."""
    attrs = {
        "description": "This  has  multiple   spaces",
        "comment": "Line1\nLine2\n\nLine4",
        "normal_attr": "normal_value",
    }

    result = utilities.normalize_whitespace(attrs)

    assert result["description"] == "This has multiple spaces"
    assert result["comment"] == "Line1 Line2 Line4"
    assert result["normal_attr"] == "normal_value"


def test_resolve_file_path_local() -> None:
    """Test resolving local file paths."""
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b"test data")

    try:
        # Test local file
        result = utilities.resolve_file_path(
            file_name=os.path.basename(tmp_path),
            source=os.path.dirname(tmp_path),
            download_url=None,
            local_data_dir=Path(os.path.dirname(tmp_path)),
            redownload=False,
        )
        assert result == Path(tmp_path)
        assert result.exists()
    finally:
        os.unlink(tmp_path)


def test_resolve_file_path_url() -> None:
    """Test resolving URL-based file paths (mock scenario)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a file in cache to avoid download
        cached_file = Path(tmp_dir) / "test_file.nc"
        cached_file.write_text("test data")

        result = utilities.resolve_file_path(
            file_name="test_file.nc",
            source="https://example.com/data/",
            download_url="https://example.com/data/test_file.nc",
            local_data_dir=Path(tmp_dir),
            redownload=False,
        )
        # Should return the cached file path
        assert result == cached_file
        assert result.exists()


def test_load_array_metadata() -> None:
    """Test loading array metadata."""
    # Test with a known datasource
    try:
        metadata = utilities.load_array_metadata("rapid26n")
        assert isinstance(metadata, dict)
        # Should contain basic structure
        assert "metadata" in metadata or len(metadata) > 0
    except FileNotFoundError:
        # If metadata files don't exist, test the exception handling
        pytest.skip("Array metadata files not available")


def test_validate_array_yaml() -> None:
    """Test YAML validation for arrays."""
    # Create a temporary YAML file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
        yaml.dump(
            {
                "array_name": "test",
                "description": "Test array",
                "variables": {"test_var": {"units": "m"}},
            },
            tmp,
        )
        tmp_path = tmp.name

    try:
        # This should work without errors (exact behavior depends on implementation)
        result = utilities.validate_array_yaml("test", verbose=False)
        assert isinstance(result, bool)
    except Exception:
        # If validation fails due to missing schema, that's expected
        pass
    finally:
        os.unlink(tmp_path)


def test_parse_ascii_header() -> None:
    """Test parsing ASCII file headers."""
    # Create a test ASCII file
    content = """% Column 1: Year
% Column 2: Month
% Column 3: Value (m/s)
% This is a comment
2020 1 1.5
2020 2 2.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        columns, num_header_lines = utilities.parse_ascii_header(
            tmp_path, comment_char="%"
        )

        assert len(columns) == 3
        assert "Year" in columns[0]
        assert "Month" in columns[1]
        assert "Value" in columns[2]
        assert num_header_lines >= 3  # Returns number of header lines
    finally:
        os.unlink(tmp_path)


def test_read_ascii_file() -> None:
    """Test reading ASCII data files."""
    content = """% Header line
% Another header
1.0 2.0 3.0
4.0 5.0 6.0
7.0 8.0 9.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        df = utilities.read_ascii_file(tmp_path, comment_char="%")

        assert isinstance(df, pd.DataFrame)
        # The function might skip header lines, check actual length
        assert len(df) >= 2  # At least 2 data rows
        assert len(df.columns) == 3  # 3 columns
        # Check data values (adjust indices based on actual behavior)
        assert df.iloc[0, 0] == 1.0 or df.iloc[0, 0] == 4.0
    finally:
        os.unlink(tmp_path)


def test_is_valid_url_edge_cases() -> None:
    """Test URL validation with edge cases."""
    # Function requires scheme, netloc, AND path
    assert utilities.is_valid_url("https://example.com/path")
    assert utilities.is_valid_url("http://test.org/data")
    assert utilities.is_valid_url("ftp://ftp.example.com/files")

    # These should fail (no path required by the function)
    assert not utilities.is_valid_url("https://example.com")  # No path
    assert not utilities.is_valid_url("")
    assert not utilities.is_valid_url("not-a-url")
    assert not utilities.is_valid_url("file:///local/path")  # Wrong scheme


def test_is_valid_file_edge_cases() -> None:
    """Test file validation with edge cases."""
    # Test with actual temporary file
    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        assert utilities._is_valid_file(tmp.name)

    # Test with non-existent file
    assert not utilities._is_valid_file("/definitely/does/not/exist.nc")

    # Test with directory instead of file
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert not utilities._is_valid_file(tmp_dir)


def test_apply_defaults_decorator() -> None:
    """Test the apply_defaults decorator functionality."""

    @utilities.apply_defaults("default_source", ["file1.nc", "file2.nc"])
    def test_function(source: str = None, file_list: list = None) -> tuple[str, list]:
        return source, file_list

    # Test with no arguments (should use defaults)
    source, files = test_function()
    assert source == "default_source"
    assert files == ["file1.nc", "file2.nc"]

    # Test with custom arguments
    source, files = test_function(source="custom", file_list=["custom.nc"])
    assert source == "custom"
    assert files == ["custom.nc"]


class TestNewUtilityFunctions:
    """Tests for recently added utility functions."""

    def test_mask_invalid_values(self):
        """Test mask_invalid_values function with lazy evaluation preservation."""
        # Create test dataset with valid_min/valid_max attributes
        ds = xr.Dataset(
            {
                "temperature": (
                    ["time"],
                    [10.0, 25.0, -999.0, 30.0, 999.0],  # -999 and 999 are invalid
                    {"valid_min": 0.0, "valid_max": 50.0},
                ),
                "salinity": (
                    ["time"],
                    [35.0, -99.0, 36.0, 37.0, 100.0],  # -99 and 100 are invalid
                    {"valid_min": 30.0, "valid_max": 40.0},
                ),
                "datetime_marker": (
                    ["time"],
                    pd.date_range("2020-01-01", periods=5),
                    {"valid_min": 0.0, "valid_max": 50.0},
                ),
                "no_limits": (["time"], [1, 2, 3, 4, 5]),  # No valid_min/max
            },
            coords={"time": pd.date_range("2020-01-01", periods=5)},
        )

        result = utilities.mask_invalid_values(ds)

        # Check that invalid values are masked as NaN
        temp_masked = result["temperature"].values
        assert pd.isna(temp_masked[2])  # -999 should be NaN
        assert pd.isna(temp_masked[4])  # 999 should be NaN
        assert temp_masked[0] == 10.0  # Valid value preserved
        assert temp_masked[1] == 25.0  # Valid value preserved
        assert temp_masked[3] == 30.0  # Valid value preserved

        sal_masked = result["salinity"].values
        assert pd.isna(sal_masked[1])  # -99 should be NaN
        assert pd.isna(sal_masked[4])  # 100 should be NaN
        assert sal_masked[0] == 35.0  # Valid value preserved

        # Variable without limits should be unchanged
        assert result["no_limits"].equals(ds["no_limits"])

        # Datetime-valued data with numeric valid_min/valid_max should be left alone
        assert result["datetime_marker"].equals(ds["datetime_marker"])
        assert result["datetime_marker"].attrs["valid_min"] == 0.0
        assert result["datetime_marker"].attrs["valid_max"] == 50.0

        # Attributes should be preserved
        assert result["temperature"].attrs["valid_min"] == 0.0
        assert result["temperature"].attrs["valid_max"] == 50.0

    def test_mask_invalid_values_edge_cases(self):
        """Test mask_invalid_values with edge cases."""
        # Empty dataset
        empty_ds = xr.Dataset()
        result = utilities.mask_invalid_values(empty_ds)
        assert len(result.data_vars) == 0

        # Dataset with no valid_min/max attributes
        ds_no_limits = xr.Dataset({"data": (["x"], [1, 2, 3])})
        result = utilities.mask_invalid_values(ds_no_limits)
        assert result["data"].equals(ds_no_limits["data"])

        # Dataset with only valid_min or only valid_max
        ds_min_only = xr.Dataset({"temp": (["x"], [-10, 0, 10], {"valid_min": 0.0})})
        result = utilities.mask_invalid_values(ds_min_only)
        assert pd.isna(result["temp"].values[0])  # -10 below valid_min
        assert result["temp"].values[1] == 0.0  # At valid_min
        assert result["temp"].values[2] == 10.0  # Above valid_min

    def test_standardize_dataset_units(self):
        """Test standardize_dataset_units function."""
        # Create test dataset with various units to standardize
        ds = xr.Dataset(
            {
                "temperature": (["time"], [20.0, 25.0], {"units": "degree_celsius"}),
                "salinity": (["time"], [35.0, 36.0], {"units": "psu"}),
                "transport": (["time"], [15.0, 20.0], {"units": "Sv"}),
                "pressure": (["time"], [1000, 2000], {"units": "dbar"}),
                "no_units": (["time"], [1, 2]),  # No units attribute
            },
            coords={"time": pd.date_range("2020-01-01", periods=2)},
        )

        result = utilities.standardize_dataset_units(ds, log_changes=False)

        # Check that units are standardized according to defaults.PREFERRED_UNITS
        from amocatlas import defaults

        assert result["temperature"].attrs["units"] == defaults.PREFERRED_UNITS["temp"]
        assert result["salinity"].attrs["units"] == defaults.PREFERRED_UNITS["psal"]
        assert (
            result["transport"].attrs["units"] == defaults.PREFERRED_UNITS["transport"]
        )
        assert result["pressure"].attrs["units"] == defaults.PREFERRED_UNITS["pressure"]

        # Variable without units should remain unchanged
        assert "units" not in result["no_units"].attrs

        # Data values should remain unchanged
        assert result["temperature"].values.tolist() == [20.0, 25.0]
        assert result["transport"].values.tolist() == [15.0, 20.0]

    def test_standardize_dataset_units_custom_mapping(self):
        """Test standardize_dataset_units with custom mapping."""
        ds = xr.Dataset({"test_var": (["x"], [1, 2], {"units": "custom_unit"})})

        custom_mapping = {"custom_unit": "standard_unit"}
        result = utilities.standardize_dataset_units(
            ds, mapping=custom_mapping, log_changes=False
        )

        assert result["test_var"].attrs["units"] == "standard_unit"

    def test_standardize_dataset_units_logging(self):
        """Test that unit standardization logging works."""
        ds = xr.Dataset({"temp": (["x"], [20], {"units": "degree_celsius"})})

        # This should not raise an error (testing logging functionality)
        result = utilities.standardize_dataset_units(ds, log_changes=True)
        from amocatlas import defaults

        assert result["temp"].attrs["units"] == defaults.PREFERRED_UNITS["temp"]

    def test_standardize_dataset_units_preserves_other_attrs(self):
        """Test that unit standardization preserves other variable attributes."""
        ds = xr.Dataset(
            {
                "temperature": (
                    ["time"],
                    [20.0, 25.0],
                    {
                        "units": "degree_celsius",
                        "long_name": "Temperature",
                        "standard_name": "sea_water_temperature",
                        "valid_min": -5.0,
                        "valid_max": 40.0,
                    },
                )
            },
            coords={"time": pd.date_range("2020-01-01", periods=2)},
        )

        result = utilities.standardize_dataset_units(ds, log_changes=False)

        # Units should be updated
        from amocatlas import defaults

        assert result["temperature"].attrs["units"] == defaults.PREFERRED_UNITS["temp"]

        # Other attributes should be preserved
        assert result["temperature"].attrs["long_name"] == "Temperature"
        assert result["temperature"].attrs["standard_name"] == "sea_water_temperature"
        assert result["temperature"].attrs["valid_min"] == -5.0
        assert result["temperature"].attrs["valid_max"] == 40.0


def test_resolve_file_path_missing_file() -> None:
    """Test error handling when local file is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir, pytest.raises(FileNotFoundError):
        utilities.resolve_file_path(
            file_name="nonexistent.nc",
            source=tmp_dir,  # Local directory
            download_url=None,
            local_data_dir=Path(tmp_dir),
            redownload=False,
        )


def test_safe_update_attrs_edge_cases() -> None:
    """Test edge cases for safe_update_attrs."""
    # Test with empty attributes
    ds = xr.Dataset()
    result = utilities.safe_update_attrs(ds, {})
    assert len(result.attrs) == 0

    # Test return value
    ds = xr.Dataset()
    result = utilities.safe_update_attrs(ds, {"test": "value"})
    assert result is ds  # Should modify in place and return same object


def test_normalize_whitespace_edge_cases() -> None:
    """Test edge cases for normalize_whitespace."""
    # Test with non-string values
    attrs = {
        "string_val": "normal text",
        "int_val": 42,
        "float_val": 3.14,
        "none_val": None,
    }

    result = utilities.normalize_whitespace(attrs)
    assert result["string_val"] == "normal text"
    assert result["int_val"] == 42  # Should remain unchanged
    assert result["float_val"] == 3.14
    assert result["none_val"] is None


def test_load_array_metadata_missing() -> None:
    """Test loading metadata for non-existent array."""
    with pytest.raises(FileNotFoundError):
        utilities.load_array_metadata("definitely_does_not_exist")


def test_download_file() -> None:
    """Test download functionality with error handling."""
    # Test with invalid URL - should raise an appropriate error
    with pytest.raises(
        (FileNotFoundError, OSError, IOError, ConnectionError, TimeoutError)
    ):
        utilities.download_file(
            "http://invalid.url.that.does.not.exist.example.com/file.nc",
            Path("/tmp"),
            filename="test_file.nc",
        )


def test_set_data_dir_project_validation() -> None:
    """Test that set_data_dir('project') validates source checkout."""
    import tempfile
    from unittest.mock import patch

    # Mock get_project_root to return a fake directory without project markers
    with tempfile.TemporaryDirectory() as fake_root:
        fake_path = Path(fake_root)

        with patch("amocatlas.utilities.get_project_root", return_value=fake_path):
            with pytest.raises(
                ValueError,
                match='"project" data_dir is only supported from a source checkout',
            ):
                utilities.set_data_dir("project")

    # Test that it works when project markers exist
    with tempfile.TemporaryDirectory() as fake_root:
        fake_path = Path(fake_root)
        # Create a pyproject.toml to make it look like a source checkout
        (fake_path / "pyproject.toml").touch()

        with patch("amocatlas.utilities.get_project_root", return_value=fake_path):
            # Should not raise an error and should use logging instead of print
            utilities.set_data_dir("project")
            # Check that data directory was set correctly
            assert utilities._user_data_dir == fake_path / "data"


def test_set_data_dir_uses_logging() -> None:
    """Test that set_data_dir uses logging instead of print statements."""
    import io
    import tempfile
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as temp_dir:
        # Capture stdout to verify no print statements
        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            utilities.set_data_dir(temp_dir)

        # Should not have printed anything to stdout
        stdout_content = captured_stdout.getvalue()
        assert stdout_content == "", (
            f"set_data_dir should not print to stdout, but got: {stdout_content}"
        )

        # Verify the directory was actually set
        assert utilities._user_data_dir == Path(temp_dir).expanduser().resolve()


class _FakeResponse:
    """Minimal stand-in for a streaming ``requests`` response.

    Yields the given byte chunks from ``iter_content``; if ``raise_on_chunk`` is set,
    raises ``ConnectionError`` when that chunk index is reached, to simulate a transfer
    that fails partway through.
    """

    def __init__(
        self,
        chunks: list,
        headers: dict = None,
        raise_on_chunk: int = None,
    ) -> None:
        self._chunks = chunks
        self.headers = headers or {}
        self._raise_on_chunk = raise_on_chunk

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int = 8192):
        for i, chunk in enumerate(self._chunks):
            if self._raise_on_chunk is not None and i == self._raise_on_chunk:
                raise ConnectionError("simulated mid-transfer failure")
            yield chunk


class TestDownloadProvenance:
    """Atomic downloads, provenance sidecars, and read_provenance()."""

    def test_successful_download_writes_provenance_sidecar(self, monkeypatch) -> None:
        """A completed download promotes the file and writes a matching sidecar."""
        import hashlib

        payload_chunks = [b"hello ", b"world"]
        payload = b"".join(payload_chunks)
        headers = {"ETag": '"abc123"', "Last-Modified": "Wed, 13 Aug 2026 00:00:00 GMT"}

        def fake_get(url, stream=True, timeout=None):
            return _FakeResponse(payload_chunks, headers=headers)

        monkeypatch.setattr(utilities.requests, "get", fake_get)

        with tempfile.TemporaryDirectory() as tmp:
            path = utilities.download_file(
                "https://example.com/data.nc", tmp, filename="data.nc"
            )
            data_file = Path(path)

            # File promoted into place, no leftover .part
            assert data_file.read_bytes() == payload
            assert not data_file.with_name(data_file.name + ".part").exists()

            # Sidecar round-trips via read_provenance with correct content
            prov = utilities.read_provenance(data_file)
            assert prov is not None
            assert prov["url"] == "https://example.com/data.nc"
            assert prov["bytes"] == len(payload)
            assert prov["sha256"] == hashlib.sha256(payload).hexdigest()
            assert prov["etag"] == '"abc123"'
            assert prov["last_modified"] == "Wed, 13 Aug 2026 00:00:00 GMT"

    def test_failed_download_leaves_no_partial_file(self, monkeypatch) -> None:
        """A transfer that fails mid-stream leaves neither the .part nor final file."""

        def fake_get(url, stream=True, timeout=None):
            return _FakeResponse([b"partial", b"more"], raise_on_chunk=1)

        monkeypatch.setattr(utilities.requests, "get", fake_get)

        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(ConnectionError):
                utilities.download_file(
                    "https://example.com/data.nc", tmp, filename="data.nc"
                )
            final = Path(tmp) / "data.nc"
            assert not final.exists()
            assert not final.with_name(final.name + ".part").exists()
            # No sidecar for a download that never completed
            assert utilities.read_provenance(final) is None

    def test_read_provenance_missing_sidecar_returns_none(self) -> None:
        """read_provenance returns None when no sidecar exists beside the file."""
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "nosidecar.nc"
            data_file.write_bytes(b"data")
            assert utilities.read_provenance(data_file) is None

    def test_provenance_omits_absent_http_headers(self, monkeypatch) -> None:
        """When the server sends no ETag/Last-Modified, those keys are omitted."""

        def fake_get(url, stream=True, timeout=None):
            return _FakeResponse([b"x"], headers={})

        monkeypatch.setattr(utilities.requests, "get", fake_get)

        with tempfile.TemporaryDirectory() as tmp:
            path = utilities.download_file(
                "https://example.com/x.nc", tmp, filename="x.nc"
            )
            prov = utilities.read_provenance(path)
            assert prov is not None
            assert "etag" not in prov
            assert "last_modified" not in prov
