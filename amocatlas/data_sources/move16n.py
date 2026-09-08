"""MOVE array data reader for AMOCatlas.

This module provides functions to read and process data from the MOVE
(Meridional Overturning Variability Experiment) observing array located
at 16°N in the Atlantic.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log  # ✅ use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "move16n"

# Default source and file list
MOVE_DEFAULT_SOURCE = (
    "https://dods.ndbc.noaa.gov/thredds/fileServer/oceansites/DATA_GRIDDED/MOVE/"
)
MOVE_DEFAULT_FILES = [
    "OS_MOVE_20000206-20221014_DPR_VOLUMETRANSPORT.nc",
    "OS_MOVE_20000101-20221021_GRD_CURRENTS-AT-SITES-MOVE3-MOVE4.nc",
    "OS_MOVE_20000101-20221018_GRD_TEMPERATURE-SALINITY-AT-SITES-MOVE1-MOVE3.nc",
]
MOVE_TRANSPORT_FILES = ["OS_MOVE_20000206-20221014_DPR_VOLUMETRANSPORT.nc"]

# Global metadata for MOVE
MOVE_METADATA = {
    "description": "MOVE transport estimates dataset from UCSD mooring project",
    "project": "Meridional Overturning Variability Experiment (MOVE)",
    "weblink": "https://dods.ndbc.noaa.gov/thredds/fileServer/oceansites/DATA_GRIDDED/MOVE/",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
    # DOI can be added here when available
    "acknowledgement": "The MOVE project is made possible with funding from the NOAA Climate Program Office. Initial funding came from the German Bundesministerium fuer Bildung und Forschung.",
}

# File-specific metadata placeholder
MOVE_FILE_METADATA = {
    "OS_MOVE_20000206-20221014_DPR_VOLUMETRANSPORT.nc": {
        "data_product": "MOVE transport time series",
        # Add specific acknowledgments here if needed in future
    },
}


@apply_defaults(MOVE_DEFAULT_SOURCE, MOVE_DEFAULT_FILES)
def read_move(
    source: str,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the MOVE transport dataset from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        URL or local path to the NetCDF file(s).
        Defaults to the MOVE data repository URL.
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to MOVE_DEFAULT_FILES.
    transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional
        If True, force redownload of the data.
    track_added_attrs : bool, optional
        If True, track which attributes were added by AMOCatlas processing.
        Returns tuple (datasets, added_attrs_per_dataset) when enabled.

    Returns
    -------
    list of xr.Dataset or tuple
        If track_added_attrs=False: List of loaded xarray datasets.
        If track_added_attrs=True: Tuple of (datasets, added_attrs_per_dataset)
        where added_attrs_per_dataset is a list of dictionaries containing
        'added' and 'modified' attribute tracking information.

    Raises
    ------
    ValueError
        If the source is neither a valid URL nor a directory path.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read MOVE dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, MOVE_METADATA
    )

    if transport_only:
        file_list = MOVE_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = ReaderUtils.setup_data_directory(data_dir)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, MOVE_FILE_METADATA)

    datasets = []
    added_attrs_per_dataset = [] if track_added_attrs else None

    netcdf_files = ReaderUtils.filter_netcdf_files(file_list)

    for file in netcdf_files:
        download_url = (
            f"{source.rstrip('/')}/{file}" if utilities.is_valid_url(source) else None
        )

        try:
            file_path = utilities.resolve_file_path(
                file_name=file,
                source=source,
                download_url=download_url,
                local_data_dir=local_data_dir,
                redownload=redownload,
            )
        except FileNotFoundError as e:
            log.warning(f"Skipping {file}: {e}")
            continue

        # Use ReaderUtils with special decode_times=False for MOVE
        # Use ReaderUtils for consistent dataset loading

        ds = ReaderUtils.safe_load_dataset(file_path, decode_times=False)

        # Clean up time variable
        if "TIME" in ds.variables:
            time_raw = ds["TIME"].values
            valid = (time_raw > 0) & (time_raw < 30000)
            n_invalid = (~valid).sum()

            if n_invalid > 0:
                log.info(
                    f"Found {n_invalid} invalid time values in {file_path}; replacing with NaN."
                )

            clean_time = xr.where(valid, time_raw, np.nan)
            base = np.datetime64("1950-01-01")
            time_converted = base + clean_time * np.timedelta64(1, "D")

            # Replace the time in the dataset
            ds["TIME"] = ("TIME", time_converted)
            ds["TIME"].attrs.update(
                {
                    "units": "days since 1950-01-01",
                }
            )
            log.debug(f"Converted time using base 1950-01-01 for {file_path}")
        else:
            log.warning(f"No TIME variable found in {file_path}")

            # Filter out NaT time values and corresponding dataset entries
            time_pd = pd.to_datetime(ds["TIME"].values)
            valid_time_mask = ~pd.isna(time_pd)

            if (~valid_time_mask).any():
                n_removed = (~valid_time_mask).sum()
                log.info(
                    f"Removing {n_removed} entries with invalid NaT time values from {file_path}"
                )

                ds = ds.isel(TIME=valid_time_mask)

        # Attach metadata with optional tracking
        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                MOVE_FILE_METADATA,
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
                MOVE_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    # Use ReaderUtils for validation
    ReaderUtils.validate_datasets_loaded(datasets, file_list)

    # Handle track_added_attrs parameter
    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
