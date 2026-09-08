"""Tests for NAC (North Atlantic Current) data reader.

Simple, targeted tests focusing on module structure and constants.
Tests the basic functionality without complex data loading mocks.
"""

from amocatlas.data_sources import nac
from amocatlas.logger import disable_logging

# Keep tests quiet
disable_logging()


class TestNAC:
    """Test basic NAC module functionality."""

    def test_module_constants_defined(self):
        """Test that all required module constants exist."""
        assert hasattr(nac, "DATASOURCE_ID")
        assert hasattr(nac, "NAC_DEFAULT_FILES")
        assert hasattr(nac, "NAC_TRANSPORT_FILES")
        assert hasattr(nac, "NAC_DEFAULT_SOURCE")
        assert hasattr(nac, "NAC_METADATA")
        assert hasattr(nac, "NAC_FILE_METADATA")

        # Check values are sensible
        assert nac.DATASOURCE_ID == "nac"
        assert isinstance(nac.NAC_DEFAULT_FILES, list)
        assert isinstance(nac.NAC_TRANSPORT_FILES, list)
        assert isinstance(nac.NAC_METADATA, dict)
        assert isinstance(nac.NAC_FILE_METADATA, dict)

    def test_default_files_configuration(self):
        """Test default files configuration is reasonable."""
        files = nac.NAC_DEFAULT_FILES
        assert len(files) > 0
        assert "bb6635909m_2_1.nc" in files

        transport_files = nac.NAC_TRANSPORT_FILES
        assert len(transport_files) > 0
        assert "bb6635909m_2_1.nc" in transport_files

        # Files should be NetCDF format for NAC data
        for file in files:
            assert file.endswith(".nc")

    def test_function_exists_and_callable(self):
        """Test that main function exists and is callable."""
        assert hasattr(nac, "read_nac")
        assert callable(nac.read_nac)

        # Check function has documentation
        func = nac.read_nac
        assert func.__doc__ is not None
        assert "North Atlantic Current" in func.__doc__ or "NAC" in func.__doc__

    def test_module_docstring_informative(self):
        """Test that module has informative docstring."""
        assert nac.__doc__ is not None
        assert "North Atlantic Current" in nac.__doc__
        assert "NAC" in nac.__doc__

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        # This test passes if the module loaded successfully
        assert nac is not None

    def test_nac_metadata_structure(self):
        """Test that NAC metadata has expected structure."""
        metadata = nac.NAC_METADATA

        # Should have expected keys
        assert "project" in metadata
        assert "weblink" in metadata
        assert "comment" in metadata

        # Values should be non-empty strings
        assert isinstance(metadata["project"], str)
        assert len(metadata["project"]) > 0
        assert isinstance(metadata["weblink"], str)
        assert len(metadata["weblink"]) > 0

    def test_nac_file_metadata_structure(self):
        """Test that NAC file metadata has expected structure."""
        file_metadata = nac.NAC_FILE_METADATA

        # Should have metadata for the default bb6635909m_2_1.nc file
        assert "bb6635909m_2_1.nc" in file_metadata

        # File metadata should have expected keys
        file_meta = file_metadata["bb6635909m_2_1.nc"]
        assert "data_product" in file_meta
        assert isinstance(file_meta["data_product"], str)
        assert len(file_meta["data_product"]) > 0

    def test_default_source_url(self):
        """Test that default source URL is properly configured."""
        source = nac.NAC_DEFAULT_SOURCE
        assert isinstance(source, str)
        assert len(source) > 0
        # Should be a valid URL-like string
        assert "http" in source or "library" in source or "/" in source
