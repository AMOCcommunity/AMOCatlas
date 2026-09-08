"""Tests for FBC (Faroe Bank Channel) data reader.

Simple, targeted tests focusing on module structure and constants.
Tests the basic functionality without complex data loading mocks.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import xarray as xr

from amocatlas.data_sources import fbc
from amocatlas.logger import disable_logging

# Keep tests quiet
disable_logging()


class TestFBC:
    """Test basic FBC module functionality."""

    def test_module_constants_defined(self):
        """Test that all required module constants exist."""
        assert hasattr(fbc, "DATASOURCE_ID")
        assert hasattr(fbc, "FBC_DEFAULT_FILES")
        assert hasattr(fbc, "FBC_TRANSPORT_FILES")

        # Check values are sensible
        assert fbc.DATASOURCE_ID == "fbc"
        assert isinstance(fbc.FBC_DEFAULT_FILES, list)
        assert isinstance(fbc.FBC_TRANSPORT_FILES, list)

    def test_default_files_configuration(self):
        """Test default files configuration is reasonable."""
        files = fbc.FBC_DEFAULT_FILES
        assert len(files) > 0
        assert "OS_GSR_FBC_D_1995_2024.nc" in files

        transport_files = fbc.FBC_TRANSPORT_FILES
        assert len(transport_files) > 0
        assert "OS_GSR_FBC_D_1995_2024.nc" in transport_files

        # Files should be NetCDF format for FBC data
        for file in files:
            assert file.endswith(".nc")

    def test_metadata_structures(self):
        """Test metadata dictionary structures."""
        # Test global metadata
        assert isinstance(fbc.FBC_METADATA, dict)
        assert "project" in fbc.FBC_METADATA
        assert "weblink" in fbc.FBC_METADATA
        assert "comment" in fbc.FBC_METADATA

        # Test file-specific metadata
        assert isinstance(fbc.FBC_FILE_METADATA, dict)
        assert "OS_GSR_FBC_D_1995_2024.nc" in fbc.FBC_FILE_METADATA
        assert "data_product" in fbc.FBC_FILE_METADATA["OS_GSR_FBC_D_1995_2024.nc"]

    def test_default_source_url(self):
        """Test default source URL configuration."""
        assert isinstance(fbc.FBC_DEFAULT_SOURCE, str)
        assert fbc.FBC_DEFAULT_SOURCE.startswith("https://")
        assert "zenodo.org" in fbc.FBC_DEFAULT_SOURCE

    def test_function_exists_and_callable(self):
        """Test that main function exists and is callable."""
        assert hasattr(fbc, "read_fbc")
        assert callable(fbc.read_fbc)

        # Check function has documentation
        func = fbc.read_fbc
        assert func.__doc__ is not None
        assert "Faroe Bank Channel" in func.__doc__ or "FBC" in func.__doc__

    def test_module_docstring_informative(self):
        """Test that module has informative docstring."""
        assert fbc.__doc__ is not None
        assert "Faroe Bank Channel" in fbc.__doc__
        assert "overflow" in fbc.__doc__
        assert "FBC" in fbc.__doc__

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        # This test passes if the module loaded successfully
        assert fbc is not None
        # Check required dependencies are accessible
        assert hasattr(fbc, "xr")  # xarray

    @patch("amocatlas.data_sources.fbc.utilities.resolve_file_path")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.safe_load_dataset")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.load_array_metadata_with_fallback")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.print_loading_info")
    def test_read_fbc_basic_functionality(
        self,
        mock_print_info,
        mock_load_metadata,
        mock_attach_metadata,
        mock_load_dataset,
        mock_resolve_path,
    ):
        """Test basic read_fbc functionality with mocked dependencies."""
        # Setup mocks
        fake_path = Path("/fake/path/OS_GSR_FBC_D_1995_2024.nc")
        mock_resolve_path.return_value = fake_path

        # Create mock dataset
        mock_ds = xr.Dataset({"transport": (["time"], [1.0, 2.0, 3.0])})
        mock_load_dataset.return_value = mock_ds
        mock_attach_metadata.return_value = mock_ds
        mock_load_metadata.return_value = ({}, {})

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test basic call
            result = fbc.read_fbc(
                source="https://example.com/",
                file_list=["OS_GSR_FBC_D_1995_2024.nc"],
                data_dir=temp_dir,
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], xr.Dataset)

            # Verify mocks were called
            mock_resolve_path.assert_called_once()
            mock_load_dataset.assert_called_once_with(fake_path)
            mock_attach_metadata.assert_called_once()

    @patch("amocatlas.data_sources.fbc.utilities.resolve_file_path")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.safe_load_dataset")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.load_array_metadata_with_fallback")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.print_loading_info")
    def test_read_fbc_transport_only_flag(
        self,
        mock_print_info,
        mock_load_metadata,
        mock_attach_metadata,
        mock_load_dataset,
        mock_resolve_path,
    ):
        """Test transport_only parameter functionality."""
        fake_path = Path("/fake/path/OS_GSR_FBC_D_1995_2024.nc")
        mock_resolve_path.return_value = fake_path
        mock_ds = xr.Dataset({"transport": (["time"], [1.0, 2.0, 3.0])})
        mock_load_dataset.return_value = mock_ds
        mock_attach_metadata.return_value = mock_ds
        mock_load_metadata.return_value = ({}, {})

        with tempfile.TemporaryDirectory() as temp_dir:
            result = fbc.read_fbc(
                source="https://example.com/",
                file_list=None,  # Test default file list
                transport_only=True,
                data_dir=temp_dir,
            )

            assert isinstance(result, list)
            assert len(result) > 0

    @patch("amocatlas.data_sources.fbc.utilities.resolve_file_path")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.safe_load_dataset")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.load_array_metadata_with_fallback")
    @patch("amocatlas.data_sources.fbc.ReaderUtils.print_loading_info")
    def test_read_fbc_track_added_attrs(
        self,
        mock_print_info,
        mock_load_metadata,
        mock_attach_metadata,
        mock_load_dataset,
        mock_resolve_path,
    ):
        """Test track_added_attrs parameter functionality."""
        fake_path = Path("/fake/path/OS_GSR_FBC_D_1995_2024.nc")
        mock_resolve_path.return_value = fake_path
        mock_ds = xr.Dataset({"transport": (["time"], [1.0, 2.0, 3.0])})
        mock_load_dataset.return_value = mock_ds

        # Mock return tuple for tracking
        mock_attach_metadata.return_value = (mock_ds, {"added": ["test_attr"]})
        mock_load_metadata.return_value = ({}, {})

        with tempfile.TemporaryDirectory() as temp_dir:
            result = fbc.read_fbc(
                source="https://example.com/",
                file_list=["OS_GSR_FBC_D_1995_2024.nc"],
                track_added_attrs=True,
                data_dir=temp_dir,
            )

            # Should return tuple when tracking attributes
            assert isinstance(result, tuple)
            assert len(result) == 2
            datasets, attr_changes = result
            assert isinstance(datasets, list)
            assert isinstance(attr_changes, list)

    def test_read_fbc_unsupported_file_type(self):
        """Test warning when unsupported file types are encountered."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch(
                "amocatlas.data_sources.fbc.ReaderUtils.load_array_metadata_with_fallback"
            ) as mock_metadata,
        ):
            mock_metadata.return_value = ({}, {})

            # Should skip unsupported files and raise error when no valid files remain
            with pytest.raises(
                FileNotFoundError,
                match="No valid data files found|Local file not found",
            ):
                fbc.read_fbc(
                    source=temp_dir,
                    file_list=["test.txt"],  # Unsupported file type
                    data_dir=temp_dir,
                )

    def test_read_fbc_no_valid_files_error(self):
        """Test error when no valid files are found."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch(
                "amocatlas.data_sources.fbc.ReaderUtils.load_array_metadata_with_fallback"
            ) as mock_metadata,
        ):
            mock_metadata.return_value = ({}, {})

            # Test with a file that will be skipped and won't be found
            with pytest.raises(
                FileNotFoundError,
                match="No valid data files found|Local file not found",
            ):
                fbc.read_fbc(
                    source=temp_dir,
                    file_list=["nonexistent.txt"],
                    data_dir=temp_dir,
                )

    @pytest.mark.slow
    def test_read_fbc_integration_with_sample_data(self):
        """Integration test: test reading with actual local sample files.

        This test is marked as 'slow' and should be run by developers before PRs
        but is excluded from CI to avoid network dependencies and flakiness.

        Run with: pytest -m slow tests/test_fbc.py
        """
        import tempfile
        from pathlib import Path

        # Create a minimal sample NetCDF file for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_file = Path(temp_dir) / "OS_GSR_FBC_D_1995_2024.nc"

            # Create minimal NetCDF file using xarray
            import numpy as np
            import pandas as pd

            # Create sample data that mimics real FBC data structure
            time_range = pd.date_range("2020-01-01", periods=5, freq="D")
            sample_data = xr.Dataset(
                {
                    "transport": (["time"], np.random.normal(2.0, 0.5, 5)),
                    "transport_error": (["time"], np.random.normal(0.1, 0.02, 5)),
                },
                coords={"time": time_range},
            )

            # Add some realistic attributes
            sample_data.attrs.update(
                {
                    "title": "Faroe Bank Channel Overflow Transport",
                    "institution": "Test Institution",
                    "source": "FBC monitoring array",
                }
            )

            # Write to NetCDF
            sample_data.to_netcdf(sample_file)

            # Now test our reader with this realistic sample file
            result = fbc.read_fbc(
                source=temp_dir,
                file_list=["OS_GSR_FBC_D_1995_2024.nc"],
                data_dir=temp_dir,
            )

            # Verify we got a dataset back
            assert isinstance(result, list)
            assert len(result) == 1

            ds = result[0]
            assert isinstance(ds, xr.Dataset)

            # Verify the data was read correctly
            assert "transport" in ds.variables
            assert "time" in ds.coords
            assert len(ds.time) == 5

            # Verify metadata was properly attached
            assert "source_file" in ds.attrs  # Should be added by standardization
            assert ds.attrs.get("title") is not None
