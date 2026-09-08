"""Tests for the SF2021 (Sanchez-Franks 2021) data reader.

These mirror the style used in other reader tests (see `test_noac47n.py`).
"""

import tempfile

import pytest

from amocatlas.data_sources import sf2021
from amocatlas.logger import disable_logging

# Keep tests quiet
disable_logging()


class TestSF2021:
    """Basic tests for the `sf2021` reader module."""

    def test_module_constants_defined(self):
        """Module exposes the expected datasource constants."""
        assert hasattr(sf2021, "DATASOURCE_ID")
        assert hasattr(sf2021, "SF2021_DEFAULT_FILES")
        assert hasattr(sf2021, "SF2021_TRANSPORT_FILES")
        assert hasattr(sf2021, "SF2021_DEFAULT_SOURCE")
        assert hasattr(sf2021, "SF2021_METADATA")
        assert hasattr(sf2021, "SF2021_FILE_METADATA")

    def test_default_files_and_transport_files(self):
        """Default and transport file lists are populated and well-formed."""
        files = sf2021.SF2021_DEFAULT_FILES
        transports = sf2021.SF2021_TRANSPORT_FILES
        assert isinstance(files, list)
        assert isinstance(transports, list)
        assert len(files) > 0
        assert len(transports) > 0
        # Expect the standard altimetry filename to be present
        assert "altimetry_moc_transport_1993_2020_18mos_smoothed.nc" in files

    def test_source_and_metadata_structure(self):
        """Default source is a URL and metadata carries the expected keys."""
        source = sf2021.SF2021_DEFAULT_SOURCE
        assert isinstance(source, str)
        assert source.startswith("http")

        metadata = sf2021.SF2021_METADATA
        assert isinstance(metadata, dict)
        for key in ("project", "weblink", "comment"):
            assert key in metadata

    def test_read_function_exists(self):
        """The public read_sf2021 entry point exists and is documented."""
        assert hasattr(sf2021, "read_sf2021")
        assert callable(sf2021.read_sf2021)
        assert sf2021.read_sf2021.__doc__ is not None

    def test_read_sf2021_raises_on_missing_local_file(self):
        """Reading a missing local file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(FileNotFoundError, match="Local file not found"):
                sf2021.read_sf2021(
                    source=tmp_dir, file_list=["nonexistent_file.nc"], data_dir=tmp_dir
                )

    def test_read_returns_dataset_and_tracks_attrs(self, monkeypatch, tmp_path):
        """read_sf2021 returns a Dataset and records tracked attribute changes."""
        import pandas as pd
        import xarray as xr

        # Minimal Dataset to be returned. Use an explicit DateOffset for
        # yearly frequency to remain compatible with newer pandas versions.
        time_index = pd.date_range("1993-01-01", periods=2, freq=pd.DateOffset(years=1))
        ds = xr.Dataset(
            {"transport": ("TIME", [1.0, 2.0])}, coords={"TIME": time_index}
        )

        fake_path = tmp_path / "altimetry_moc_transport_1993_2020_18mos_smoothed.nc"
        fake_path.write_text("fake")

        monkeypatch.setattr(
            "amocatlas.utilities.resolve_file_path",
            lambda file_name, source, download_url, local_data_dir, redownload=False: (
                fake_path
            ),
        )

        monkeypatch.setattr(
            "amocatlas.data_sources.sf2021.ReaderUtils.safe_load_dataset",
            lambda p: ds,
        )

        def fake_attach(
            ds_in,
            file,
            file_path,
            global_meta,
            yaml_file_meta,
            file_meta,
            ds_id,
            track_added_attrs=False,
        ):
            if track_added_attrs:
                return ds_in, {"added": ["source_file"]}
            return ds_in

        monkeypatch.setattr(
            "amocatlas.data_sources.sf2021.ReaderUtils.attach_metadata_with_tracking",
            fake_attach,
        )

        datasets, added = sf2021.read_sf2021(
            source=None, file_list=None, track_added_attrs=True, data_dir=tmp_path
        )

        assert isinstance(datasets, list)
        assert len(datasets) == 1
        assert isinstance(datasets[0], xr.Dataset)
        assert "TIME" in datasets[0].coords
        assert isinstance(added, list)
        assert isinstance(added[0], dict)

    def test_normalize_sf2021_time_coordinate(self):
        """Test that TIME coordinate is correctly converted from days since 0000-01-01 to datetime64[ns]."""
        import numpy as np
        import xarray as xr

        # Create a dataset with sat_time as float (days since 0000-01-01)
        # 727945.0 days since 0000-01-01 should be approximately 1993-01-17
        time_values = np.array([727945.0, 727974.5, 728004.0])
        ds = xr.Dataset(
            {"MOC_PROXY": ("sat_time", [1.0, 2.0, 3.0])},
            coords={"sat_time": time_values},
        )

        # Apply the conversion function
        ds_converted = sf2021._normalize_sf2021_time_coordinate(
            ds, source_file="altimetry_moc_transport_1993_2020_18mos_smoothed.nc"
        )

        # Verify the conversion happened
        assert "sat_time" in ds_converted.coords
        assert ds_converted["sat_time"].dtype == np.dtype("datetime64[ns]")

        # Verify the dates are correct (1993, not 1970)
        first_date = ds_converted["sat_time"].values[0]
        first_date_str = str(first_date)
        assert "1993" in first_date_str, f"Expected 1993 in date, got {first_date_str}"

        # Verify metadata was set
        assert "units" in ds_converted["sat_time"].attrs
        assert "standard_name" in ds_converted["sat_time"].attrs
        assert ds_converted["sat_time"].attrs["standard_name"] == "time"

    def test_normalize_sf2021_time_coordinate_with_TIME_name(self):
        """Test that TIME coordinate conversion works when variable is already named TIME."""
        import numpy as np
        import xarray as xr

        # Create a dataset with TIME as float (days since 0000-01-01)
        time_values = np.array([727945.0, 727974.5, 728004.0])
        ds = xr.Dataset(
            {"MOC_PROXY": ("TIME", [1.0, 2.0, 3.0])}, coords={"TIME": time_values}
        )

        # Apply the conversion function
        ds_converted = sf2021._normalize_sf2021_time_coordinate(
            ds, source_file="altimetry_moc_transport_1993_2020_18mos_smoothed.nc"
        )

        # Verify the conversion happened on TIME coordinate
        assert "TIME" in ds_converted.coords
        assert ds_converted["TIME"].dtype == np.dtype("datetime64[ns]")

        # Verify the dates are correct and the fractional 0.5 day is preserved.
        converted_times = ds_converted["TIME"].values
        assert str(converted_times[0]) == "1993-01-17T00:00:00.000000000"
        assert str(converted_times[1]) == "1993-02-15T12:00:00.000000000"
        assert str(converted_times[2]) == "1993-03-17T00:00:00.000000000"
        assert converted_times[1] - converted_times[0] == np.timedelta64(
            29, "D"
        ) + np.timedelta64(12, "h")
