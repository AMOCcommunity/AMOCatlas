"""Zheng et al. 2024 freshwater transport data reader for AMOCatlas.

This module provides functions to read and process freshwater transport data
from Zheng et al. (2024). This dataset provides observations and estimates
of freshwater transport across key sections in the Atlantic Ocean, which is
closely related to AMOC variability and climate change.
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
DATASOURCE_ID = "zheng2024"

# Default list of ZHENG2024 (Atlantic meridional freshwater transport) data files
ZHENG2024_DEFAULT_FILES = ["atl_mft_2000_extend_gpcp_oaflux.nc"]
ZHENG2024_TRANSPORT_FILES = ["atl_mft_2000_extend_gpcp_oaflux.nc"]
ZHENG2024_DEFAULT_SOURCE = "https://zenodo.org/records/12790901/files/"

ZHENG2024_METADATA = {
    "project": "An observation-based estimate of the Atlantic meridional freshwater transport",
    "weblink": "https://zenodo.org/records/12790901",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

ZHENG2024_FILE_METADATA = {
    "atl_mft_2000_extend_gpcp_oaflux.nc": {
        "data_product": "An observation-based estimate of the Atlantic meridional freshwater transport",
    }
}


@apply_defaults(ZHENG2024_DEFAULT_SOURCE, ZHENG2024_DEFAULT_FILES)
def read_zheng2024(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the ZHENG2024 transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).

    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to ZHENG2024_DEFAULT_FILES.

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
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read ZHENG2024 dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, ZHENG2024_METADATA
    )

    # Ensure file_list has a default
    if file_list is None:
        file_list = ZHENG2024_DEFAULT_FILES
    if transport_only:
        file_list = ZHENG2024_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]
    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, ZHENG2024_FILE_METADATA)

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
                    ZHENG2024_FILE_METADATA,
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
                    ZHENG2024_FILE_METADATA,
                    DATASOURCE_ID,
                    track_added_attrs=False,
                )
        else:
            raise ValueError(
                f"Unsupported file type for {file}. Only .nc files are supported."
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid ZHENG2024 files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d ZHENG2024 dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
