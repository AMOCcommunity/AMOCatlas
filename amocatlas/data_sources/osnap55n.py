"""OSNAP array data reader for AMOCatlas.

This module provides functions to read and process data from the OSNAP
(Overturning in the Subpolar North Atlantic Program) observing array.

"""

from pathlib import Path

import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_error
from amocatlas.reader_utils import ReaderUtils

log = logger.log  # Use global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "osnap55n"

# Default file list - 2020 version (legacy)
OSNAP_DEFAULT_FILES = [
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc",
    "OSNAP_Streamfunction_201408_202006_2023.nc",
    "OSNAP_Gridded_TSV_201408_202006_2023.nc",
]
OSNAP_TRANSPORT_FILES = ["OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc"]

# 2025 file list - extended coverage 2014-2022
OSNAP_2025_DEFAULT_FILES = [
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202207_2025.nc",
    "OSNAP_Streamfunction_201408_202207_2025.nc",
    "OSNAP_Gridded_TSV_201408_202207_2025.nc",
]
OSNAP_2025_TRANSPORT_FILES = ["OSNAP_MOC_MHT_MFT_TimeSeries_201408_202207_2025.nc"]

# Mapping of filenames to download URLs
OSNAP_FILE_URLS = {
    # Legacy 2020 files
    "README_OSNAP-MOC_202306.doc": "https://repository.gatech.edu/bitstreams/930261ff-6cca-4cf9-81c8-d27c51a4ca49/download",
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/e039e311-dd2e-4511-a525-c2fcfb3be85a/download",
    "OSNAP_Streamfunction_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/5edf4cba-a28f-40a6-a4da-24d7436a42ab/download",
    "OSNAP_Gridded_TSV_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/598f200a-50ba-4af0-96af-bd29fe692cdc/download",
    # 2025 files - extended coverage 2014-2022
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202207_2025.nc": "https://repository.gatech.edu/bitstreams/597db471-e2ea-4109-b1a1-b94451f1b884/download",
    "OSNAP_Streamfunction_201408_202207_2025.nc": "https://repository.gatech.edu/bitstreams/f82339f6-2145-456d-9a53-f3ede32b76a3/download",
    "OSNAP_Gridded_TSV_201408_202207_2025.nc": "https://repository.gatech.edu/bitstreams/af6a47f7-f705-49b4-a64f-5cd086b9b9fb/download",
}

# General metadata (global for OSNAP)
OSNAP_METADATA = {
    "project": "Overturning in the Subpolar North Atlantic Program (OSNAP)",
    "weblink": "https://www.o-snap.org",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
    "acknowledgement": "OSNAP data were collected and made freely available by the OSNAP (Overturning in the Subpolar North Atlantic Program) project and all the national programs that contribute to it (www.o-snap.org).",
    "doi": "https://doi.org/10.35090/gatech/70342",
}

# File-specific metadata (placeholder, ready to extend)
OSNAP_FILE_METADATA = {
    # Legacy 2020 files
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc": {
        "data_product": "Time series of MOC, MHT, and MFT",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2020-06-30",
    },
    "OSNAP_Streamfunction_201408_202006_2023.nc": {
        "data_product": "Meridional overturning streamfunction",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2020-06-30",
    },
    "OSNAP_Gridded_TSV_201408_202006_2023.nc": {
        "data_product": "Gridded temperature, salinity, and velocity",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2020-06-30",
    },
    # 2025 files - extended coverage
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202207_2025.nc": {
        "data_product": "Time series of MOC, MHT, and MFT (2014-2022)",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2022-07-31",
        "dataset_version": "2025",
        "processing_software": "MATLAB R2024b",
    },
    "OSNAP_Streamfunction_201408_202207_2025.nc": {
        "data_product": "Meridional overturning streamfunction (2014-2022)",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2022-07-31",
        "dataset_version": "2025",
        "processing_software": "MATLAB R2024b",
    },
    "OSNAP_Gridded_TSV_201408_202207_2025.nc": {
        "data_product": "Gridded velocity, temperature, and salinity (2014-2022)",
        "time_coverage_start": "2014-08-01",
        "time_coverage_end": "2022-07-31",
        "dataset_version": "2025",
        "processing_software": "MATLAB R2024b",
        "file_size": "55.98 MB",
    },
}


def read_osnap(
    source: str = None,
    file_list: str | list[str] = None,
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    version: str = "2025",
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the OSNAP transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults depend on version: OSNAP_2025_DEFAULT_FILES for "2025",
        OSNAP_DEFAULT_FILES for "2020".
    transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional
        If True, force redownload of the data.
    version : str, optional
        Dataset version to use ("2025" for 2014-2022 data, "2020" for 2014-2020 data).
        Defaults to "2025" (latest version).
    track_added_attrs : bool, optional
        If True, track which attributes were added during metadata enrichment.

    Returns
    -------
    list of xr.Dataset
        List of loaded xarray datasets with basic inline and file-specific metadata.

    Raises
    ------
    ValueError
        If an invalid version is specified.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read OSNAP dataset (version %s)", version)

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, OSNAP_METADATA
    )

    # Select appropriate file lists based on version
    if version == "2025":
        default_files = OSNAP_2025_DEFAULT_FILES
        transport_files = OSNAP_2025_TRANSPORT_FILES
    elif version == "2020":
        default_files = OSNAP_DEFAULT_FILES
        transport_files = OSNAP_TRANSPORT_FILES
    else:
        raise ValueError(f"Invalid version '{version}'. Must be '2020' or '2025'.")

    # Ensure file_list has a default
    if file_list is None:
        file_list = default_files
    if transport_only:
        file_list = transport_files
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = ReaderUtils.setup_data_directory(data_dir)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, OSNAP_FILE_METADATA)

    datasets = []

    added_attrs_per_dataset = [] if track_added_attrs else None
    netcdf_files = ReaderUtils.filter_netcdf_files(file_list)

    for file in netcdf_files:
        download_url = OSNAP_FILE_URLS.get(file)
        if not download_url:
            log_error("No download URL defined for OSNAP file: %s", file)
            raise FileNotFoundError(f"No download URL defined for OSNAP file {file}")

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # Use ReaderUtils for consistent dataset loading
        ds = ReaderUtils.safe_load_dataset(file_path)

        # Attach metadata with optional tracking

        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                OSNAP_FILE_METADATA,
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
                OSNAP_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    # Use ReaderUtils for validation
    ReaderUtils.validate_datasets_loaded(datasets, file_list)

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets


def read_osnap_2025(
    source: str = None,
    file_list: str | list[str] = None,
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the OSNAP 2025 datasets (2014-2022 coverage) from a URL or local file path.

    This is a convenience function that calls read_osnap with version="2025".

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to OSNAP_2025_DEFAULT_FILES.
    transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional
        If True, force redownload of the data.

    Returns
    -------
    list of xr.Dataset
        List of loaded xarray datasets with basic inline and file-specific metadata.

    """
    return read_osnap(
        source=source,
        file_list=file_list,
        transport_only=transport_only,
        data_dir=data_dir,
        redownload=redownload,
        version="2025",
    )
