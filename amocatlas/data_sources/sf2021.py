"""Sanchez-Franks Satellite proxy for the AMOC at 26N data reader for AMOCatlas.

This module provides functions to read and process satellite proxy transport data for 26N
from Sanchez-Franks et al. (2021). This dataset provides a satellite reconstruction of the AMOC transport
at 26N based on satellite altimetry. It also includes the upper-mid-ocean and gulf stream components.
The components are derived through a dynamically based method.
"""

from pathlib import Path

import numpy as np
import xarray as xr

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_debug, log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "sf2021"

# Default list of SF2021 (Sanchez-Franks 2021) data files
SF2021_DEFAULT_FILES = ["altimetry_moc_transport_1993_2020_18mos_smoothed.nc"]
SF2021_TRANSPORT_FILES = ["altimetry_moc_transport_1993_2020_18mos_smoothed.nc"]
SF2021_DEFAULT_SOURCE = "https://zenodo.org/records/18941523/files/"

SF2021_METADATA = {
    "project": "A satellite reconstruction of the AMOC transport at 26N",
    "weblink": "https://zenodo.org/records/18941523",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

SF2021_FILE_METADATA = {
    "altimetry_moc_transport_1993_2020_18mos_smoothed.nc": {
        "data_product": "A satellite reconstruction of the AMOC transport at 26N",
    }
}

# Metadata for time coordinate
_TIME_METADATA = {
    "units": "seconds since 1970-01-01T00:00:00Z",
    "long_name": "Time elapsed since 1970-01-01T00:00:00Z",
    "standard_name": "time",
    "calendar": "gregorian",
    "vocabulary": "http://vocab.nerc.ac.uk/collection/OG1/current/TIME/",
}


def _normalize_sf2021_time_coordinate(
    ds: xr.Dataset, source_file: str = None
) -> xr.Dataset:
    """Convert SF2021 TIME coordinate from days since 0000-01-01 to datetime64[ns].

    Parameters
    ----------
    ds : xr.Dataset
        Dataset with sat_time or TIME coordinate as float (days since 0000-01-01)
    source_file : str, optional
        Source filename, included in debug/warning log messages for provenance.

    Returns
    -------
    xr.Dataset
        Dataset with time coordinate converted to datetime64[ns]

    """
    file_context = f" ({source_file})" if source_file else ""

    # Find time variable (check raw name first, then final name)
    time_var = next((var for var in ["sat_time", "TIME"] if var in ds.coords), None)

    if not time_var or ds[time_var].dtype.kind not in ["f", "i"]:
        log_debug(
            f"Skipping TIME normalization{file_context} - "
            f"{time_var or 'TIME'} not found or not numeric"
        )
        return ds

    try:
        # Convert days since 0000-01-01 to datetime64[ns] without using year 0 in ns resolution.
        # Decompose into integer days and fractional nanoseconds relative to 1970-01-01.
        time_values = np.asarray(ds[time_var].values, dtype=np.float64)
        epoch_days = 719528.0  # Days between 0000-01-01 and 1970-01-01 in proleptic Gregorian calendar.
        relative_days = time_values - epoch_days
        whole_days = np.floor(relative_days).astype(np.int64)
        fractional_ns = np.rint((relative_days - whole_days) * 86400 * 1e9).astype(
            np.int64
        )

        time_datetime = (
            np.datetime64("1970-01-01", "ns")
            + whole_days.astype("timedelta64[D]")
            + fractional_ns.astype("timedelta64[ns]")
        ).astype("datetime64[ns]")

        # Use assign_coords to properly set dimension coordinate
        ds = ds.assign_coords({time_var: time_datetime})
        ds[time_var].attrs = _TIME_METADATA
        log_debug(
            f"Converted SF2021 {time_var} from days to datetime64[ns]{file_context}"
        )
    except (ValueError, TypeError, OverflowError) as e:
        log_warning(f"Failed to convert SF2021 TIME coordinate{file_context}: {e}")

    return ds


@apply_defaults(SF2021_DEFAULT_SOURCE, SF2021_DEFAULT_FILES)
def read_sf2021(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the SF2021 transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).

    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to SF2021_DEFAULT_FILES.

    transport_only : bool, optional
        If True, restrict to transport files only.

    data_dir : str, Path or None, optional
        Optional local data directory.

    redownload : bool, optional
        If True, force redownload of the data.
    track_added_attrs : bool, optional
        If True, track which attributes were added during metadata enrichment.

    Returns
    -------
    list of xr.Dataset
        List of loaded xarray datasets with basic inline and file-specific metadata.

    Raises
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read SF2021 dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, SF2021_METADATA
    )

    # Ensure file_list has a default
    if file_list is None:
        file_list = SF2021_DEFAULT_FILES
    if transport_only:
        file_list = SF2021_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]
    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, SF2021_FILE_METADATA)

    datasets = []

    added_attrs_per_dataset = [] if track_added_attrs else None
    for file in file_list:
        if not (file.lower().endswith(".nc")):
            log_warning("Skipping unsupported file type : %s", file)
            continue

        download_url = (
            f"{source.rstrip('/')}/{file}" if utilities.is_valid_url(source) else None
        )

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # Open dataset

        if file.lower().endswith(".nc"):
            # Use ReaderUtils for consistent dataset loading

            ds = ReaderUtils.safe_load_dataset(file_path)

            # Attach metadata
            # Attach metadata with optional tracking

            if track_added_attrs:
                ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                    ds,
                    file,
                    file_path,
                    global_metadata,
                    yaml_file_metadata,
                    SF2021_FILE_METADATA,
                    DATASOURCE_ID,
                    track_added_attrs=True,
                )

                added_attrs_per_dataset.append(attr_changes)

            else:
                ds = ReaderUtils.attach_metadata_with_tracking(
                    ds,
                    file,
                    file_path,
                    global_metadata,
                    yaml_file_metadata,
                    SF2021_FILE_METADATA,
                    DATASOURCE_ID,
                    track_added_attrs=False,
                )

            # Normalize SF2021 TIME coordinate AFTER metadata attachment
            ds = _normalize_sf2021_time_coordinate(ds, source_file=file)
        else:
            raise ValueError(
                f"Unsupported file type for {file}. Only .nc files are supported."
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid SF2021 files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d SF2021 dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
