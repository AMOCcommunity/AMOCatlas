"""North Atlantic Current (NAC) data reader for AMOCatlas.

This module provides functions to read and process the North Atlantic current time series from satellite and float observations.
The NAC is a key component of the Atlantic Meridional Overturning Circulation, transporting warm, saline water from the tropics to the high northern latitudes.

The dataset includes NAC transport estimates from satellite and float observations and an NAC estimation from satellite altimetry alone.

Key functions:
- read_nac(): Main data loading interface for North Atlantic Current data

Data source: Satellite and float observations
Location: Between tip of Greenland and northern Spain
"""

from pathlib import Path

import xarray as xr

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "nac"

# Default list of NAC data files.
#
# The UCSD Digital Collections object serves this file under the internal
# component id "_2_1.nc" (the prefixed URL .../bb6635909m/bb6635909m_2_1.nc
# 404s), but the HTTP Content-Disposition names it "bb6635909m_2_1.nc". We save,
# key metadata, and report it under that fuller name — which includes the object
# id and matches what a browser download produces — and map back to the internal
# id only when building the download URL (NAC_URL_PATH_SEGMENT below).
NAC_DEFAULT_FILES = ["bb6635909m_2_1.nc"]
NAC_TRANSPORT_FILES = ["bb6635909m_2_1.nc"]
NAC_DEFAULT_SOURCE = "https://library.ucsd.edu/dc/object/bb6635909m"

# Map the saved/reported filename to the URL path segment served by UCSD.
NAC_URL_PATH_SEGMENT = {"bb6635909m_2_1.nc": "_2_1.nc"}

NAC_METADATA = {
    "project": "North Atlantic Current Time Series from Satellite and Float Observations (1993-2025)",
    "weblink": "https://library.ucsd.edu/dc/object/bb6635909m",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

NAC_FILE_METADATA = {
    "bb6635909m_2_1.nc": {
        "data_product": "6-monthly estimates of NAC transport from satellite altimetry and float observations",
    },
}


@apply_defaults(NAC_DEFAULT_SOURCE, NAC_DEFAULT_FILES)
def read_nac(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the NAC (North Atlantic Current) transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).

    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to NAC_DEFAULT_FILES.

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
        And if track_added_attrs is True, also returns a list of dictionaries with the attributes that were added to each dataset during metadata enrichment.

    Raises
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.

    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read NAC dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, NAC_METADATA
    )

    # Ensure file_list has a default
    if file_list is None:
        file_list = NAC_DEFAULT_FILES
    if transport_only:
        file_list = NAC_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]
    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, NAC_FILE_METADATA)

    datasets = []

    added_attrs_per_dataset = [] if track_added_attrs else None
    for file in file_list:
        if not (file.lower().endswith(".nc")):
            log_warning("Skipping unsupported file type : %s", file)
            continue

        # The saved/reported name (file) carries the object id; the download URL
        # must use the internal component id served by UCSD.
        url_segment = NAC_URL_PATH_SEGMENT.get(file, file)
        download_url = (
            f"{source.rstrip('/')}/{url_segment}"
            if utilities.is_valid_url(source)
            else None
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
                    NAC_FILE_METADATA,
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
                    NAC_FILE_METADATA,
                    DATASOURCE_ID,
                    track_added_attrs=False,
                )
        else:
            raise ValueError(
                f"Unsupported file type for {file}. Only .nc files are supported."
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid NAC files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d NAC dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
