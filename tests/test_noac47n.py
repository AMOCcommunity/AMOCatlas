"""Tests for NOAC 47°N array data reader.

Simple, targeted tests focusing on module structure and constants.
Tests the basic functionality without complex data loading mocks.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import xarray as xr

from amocatlas.data_sources import noac47n
from amocatlas.logger import disable_logging

# Keep tests quiet
disable_logging()


class TestNOAC47N:
    """Test basic NOAC 47°N module functionality."""

    def test_module_constants_defined(self):
        """Test that all required module constants exist."""
        assert hasattr(noac47n, "DATASOURCE_ID")
        assert hasattr(noac47n, "NOAC47N_DEFAULT_FILES")
        assert hasattr(noac47n, "NOAC47N_TRANSPORT_FILES")
        assert hasattr(noac47n, "A47N_DEFAULT_SOURCE")
        assert hasattr(noac47n, "A47N_METADATA")

        # Check values are sensible
        assert noac47n.DATASOURCE_ID == "noac47n"
        assert isinstance(noac47n.NOAC47N_DEFAULT_FILES, list)
        assert isinstance(noac47n.A47N_METADATA, dict)

    def test_default_files_configuration(self):
        """Test default files configuration is reasonable."""
        files = noac47n.NOAC47N_DEFAULT_FILES
        assert len(files) > 0
        assert "NOAC_AMOC.tab" in files

        transport_files = noac47n.NOAC47N_TRANSPORT_FILES
        assert len(transport_files) > 0
        assert "NOAC_AMOC.tab" in transport_files

        # Files should be tab format
        for file in files:
            assert file.endswith(".tab")

    def test_source_configuration(self):
        """Test data source configuration."""
        source = noac47n.A47N_DEFAULT_SOURCE
        assert isinstance(source, str)
        assert source.startswith("https://")
        assert "doi" in source or "pangaea" in source.lower()

    def test_file_urls_configuration(self):
        """Test file URL mapping configuration."""
        file_urls = noac47n.A47N_FILE_URLS
        assert isinstance(file_urls, dict)
        assert "NOAC_AMOC.tab" in file_urls

        # Check URL format
        for _filename, url in file_urls.items():
            assert isinstance(url, str)
            assert url.startswith("https://")

    def test_file_metadata_structure(self):
        """Test file-specific metadata structure."""
        file_metadata = noac47n.A47N_FILE_METADATA
        assert isinstance(file_metadata, dict)
        assert "NOAC_AMOC.tab" in file_metadata

        for _filename, metadata in file_metadata.items():
            assert isinstance(metadata, dict)
            assert "data_product" in metadata

    def test_metadata_structure(self):
        """Test metadata structure is reasonable."""
        metadata = noac47n.A47N_METADATA
        assert isinstance(metadata, dict)

        # Check for expected keys
        expected_keys = ["project", "weblink", "comment"]
        for key in expected_keys:
            assert key in metadata, f"Expected metadata key '{key}' not found"

        # Check values are non-empty strings
        for _key, value in metadata.items():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_function_exists_and_callable(self):
        """Test that main function exists and is callable."""
        assert hasattr(noac47n, "read_47n")
        assert callable(noac47n.read_47n)

        # Check function has documentation
        func = noac47n.read_47n
        assert func.__doc__ is not None
        assert "47" in func.__doc__ or "NOAC" in func.__doc__

    def test_module_docstring_informative(self):
        """Test that module has informative docstring."""
        assert noac47n.__doc__ is not None
        assert "NOAC" in noac47n.__doc__
        assert "47°N" in noac47n.__doc__ or "47N" in noac47n.__doc__

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        # This test passes if the module loaded successfully
        assert noac47n is not None
        # Check required dependencies are accessible
        assert hasattr(noac47n, "xr")  # xarray
        assert hasattr(noac47n, "pd")  # pandas

    def _create_mock_tab_file_content(self):
        """Helper to create mock TAB file content."""
        header = "\n".join([f"# Header line {i}" for i in range(31)])
        data = "Date/Time\tMOC_transport\n2000-01-01\t15.2\n2000-06-01\t14.8\n2001-01-01\t16.1"
        return header + "\n" + data

    @patch("amocatlas.data_sources.noac47n.utilities.resolve_file_path")
    @patch(
        "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
    )
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.print_loading_info")
    def test_read_47n_basic_functionality(
        self,
        mock_print_info,
        mock_attach_metadata,
        mock_load_metadata,
        mock_resolve_path,
    ):
        """Test basic read_47n functionality with mocked file."""
        # Setup mocks
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock file content
            mock_content = self._create_mock_tab_file_content()
            fake_file = Path(temp_dir) / "NOAC_AMOC.tab"
            fake_file.write_text(mock_content)

            mock_resolve_path.return_value = fake_file
            mock_load_metadata.return_value = ({}, {})

            # Mock dataset to return from attach_metadata
            mock_ds = xr.Dataset({"MOC_transport": (["TIME"], [15.2, 14.8, 16.1])})
            mock_attach_metadata.return_value = mock_ds

            # Test basic call
            result = noac47n.read_47n(
                source="https://example.com/",
                file_list=["NOAC_AMOC.tab"],
                data_dir=temp_dir,
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], xr.Dataset)

            # Verify mocks were called
            mock_resolve_path.assert_called_once()
            mock_attach_metadata.assert_called_once()

    @patch("amocatlas.data_sources.noac47n.utilities.resolve_file_path")
    @patch(
        "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
    )
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.print_loading_info")
    def test_read_47n_transport_only_flag(
        self,
        mock_print_info,
        mock_attach_metadata,
        mock_load_metadata,
        mock_resolve_path,
    ):
        """Test transport_only parameter functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_content = self._create_mock_tab_file_content()
            fake_file = Path(temp_dir) / "NOAC_AMOC.tab"
            fake_file.write_text(mock_content)

            mock_resolve_path.return_value = fake_file
            mock_load_metadata.return_value = ({}, {})
            mock_ds = xr.Dataset({"MOC_transport": (["TIME"], [15.2, 14.8, 16.1])})
            mock_attach_metadata.return_value = mock_ds

            result = noac47n.read_47n(
                source="https://example.com/",
                file_list=None,  # Test default file list
                transport_only=True,
                data_dir=temp_dir,
            )

            assert isinstance(result, list)
            assert len(result) > 0

    @patch("amocatlas.data_sources.noac47n.utilities.resolve_file_path")
    @patch(
        "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
    )
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.attach_metadata_with_tracking")
    @patch("amocatlas.data_sources.noac47n.ReaderUtils.print_loading_info")
    def test_read_47n_track_added_attrs(
        self,
        mock_print_info,
        mock_attach_metadata,
        mock_load_metadata,
        mock_resolve_path,
    ):
        """Test track_added_attrs parameter functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_content = self._create_mock_tab_file_content()
            fake_file = Path(temp_dir) / "NOAC_AMOC.tab"
            fake_file.write_text(mock_content)

            mock_resolve_path.return_value = fake_file
            mock_load_metadata.return_value = ({}, {})
            mock_ds = xr.Dataset({"MOC_transport": (["TIME"], [15.2, 14.8, 16.1])})

            # Mock return tuple for tracking
            mock_attach_metadata.return_value = (mock_ds, {"added": ["test_attr"]})

            result = noac47n.read_47n(
                source="https://example.com/",
                file_list=["NOAC_AMOC.tab"],
                track_added_attrs=True,
                data_dir=temp_dir,
            )

            # Should return tuple when tracking attributes
            assert isinstance(result, tuple)
            assert len(result) == 2
            datasets, attr_changes = result
            assert isinstance(datasets, list)
            assert isinstance(attr_changes, list)

    def test_read_47n_no_download_url_error(self):
        """Test error handling when no download URL is found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
            ) as mock_metadata:
                mock_metadata.return_value = ({}, {})

                # Patch the FILE_URLS to not contain our test file
                with (
                    patch.dict(
                        "amocatlas.data_sources.noac47n.A47N_FILE_URLS", {}, clear=True
                    ),
                    pytest.raises(ValueError, match="No download URL found for file"),
                ):
                    noac47n.read_47n(
                        source="https://example.com/",
                        file_list=["nonexistent_file.tab"],
                        data_dir=temp_dir,
                    )

    def test_read_47n_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
            ) as mock_metadata:
                mock_metadata.return_value = ({}, {})

                # Should skip unsupported files and potentially raise error if no valid files remain
                with pytest.raises(
                    FileNotFoundError,
                    match="No valid data files found|Local file not found",
                ):
                    noac47n.read_47n(
                        source=temp_dir,
                        file_list=["test.nc"],  # Wrong file type
                        data_dir=temp_dir,
                    )

    @pytest.mark.slow
    def test_read_47n_integration_with_sample_data(self):
        """Integration test: test reading with actual local sample files.

        This test is marked as 'slow' and should be run by developers before PRs
        but is excluded from CI to avoid network dependencies and flakiness.

        Run with: pytest -m slow tests/test_noac47n.py
        """
        import tempfile
        from pathlib import Path

        # Create a minimal sample TAB file for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_file = Path(temp_dir) / "NOAC_AMOC.tab"

            # Create sample TAB file content that mimics real NOAC data
            header_lines = [f"# Header line {i}" for i in range(31)]
            data_lines = [
                "Date/Time\tMOC_transport\tMOC_error",
                "2020-01-01\t15.2\t0.8",
                "2020-06-01\t14.8\t0.9",
                "2021-01-01\t16.1\t0.7",
            ]

            content = "\n".join(header_lines + data_lines)
            sample_file.write_text(content)

            # Test our reader with this realistic sample file
            # Patch the download URL mapping to use local file
            with patch.dict(
                "amocatlas.data_sources.noac47n.A47N_FILE_URLS",
                {"NOAC_AMOC.tab": f"file://{sample_file}"},
                clear=True,
            ):
                result = noac47n.read_47n(
                    source=temp_dir, file_list=["NOAC_AMOC.tab"], data_dir=temp_dir
                )

            # Verify we got a dataset back
            assert isinstance(result, list)
            assert len(result) == 1

            ds = result[0]
            assert isinstance(ds, xr.Dataset)

            # Verify the data was read correctly
            assert "MOC_transport" in ds.variables
            assert "TIME" in ds.coords
            assert len(ds.TIME) == 3

            # Verify time conversion worked
            assert ds["TIME"].dtype.kind == "M"  # datetime64 type

            # Verify metadata was properly attached
            assert "source_file" in ds.attrs  # Should be added by standardization

    @patch("amocatlas.data_sources.noac47n.utilities.resolve_file_path")
    @patch(
        "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
    )
    def test_read_47n_file_parsing_error(self, mock_load_metadata, mock_resolve_path):
        """Test error handling when file parsing fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted file
            corrupted_file = Path(temp_dir) / "NOAC_AMOC.tab"
            corrupted_file.write_text("invalid\tcontent\nwithout\tproper\tformat")

            mock_resolve_path.return_value = corrupted_file
            mock_load_metadata.return_value = ({}, {})

            with pytest.raises(FileNotFoundError, match="Failed to parse ASCII file"):
                noac47n.read_47n(
                    source="https://example.com/",
                    file_list=["NOAC_AMOC.tab"],
                    data_dir=temp_dir,
                )

    @patch("amocatlas.data_sources.noac47n.utilities.resolve_file_path")
    @patch(
        "amocatlas.data_sources.noac47n.ReaderUtils.load_array_metadata_with_fallback"
    )
    def test_read_47n_dataframe_conversion_error(
        self, mock_load_metadata, mock_resolve_path
    ):
        """Test error handling when DataFrame to xarray conversion fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with invalid time format
            header = "\n".join([f"# Header line {i}" for i in range(31)])
            invalid_data = "Date/Time\tMOC_transport\ninvalid_date\t15.2"
            mock_content = header + "\n" + invalid_data

            invalid_file = Path(temp_dir) / "NOAC_AMOC.tab"
            invalid_file.write_text(mock_content)

            mock_resolve_path.return_value = invalid_file
            mock_load_metadata.return_value = ({}, {})

            with pytest.raises(
                ValueError, match="Failed to convert DataFrame to xarray Dataset"
            ):
                noac47n.read_47n(
                    source="https://example.com/",
                    file_list=["NOAC_AMOC.tab"],
                    data_dir=temp_dir,
                )
