from pathlib import Path
from typing import Union

import xarray as xr

from amocatlas import logger, utilities
from amocatlas.utilities import apply_defaults

log = logger.log  # Use global logger

# Default file list
OSNAP_DEFAULT_FILES = [
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc",
    "OSNAP_Streamfunction_201408_202006_2023.nc",
    "OSNAP_Gridded_TSV_201408_202006_2023.nc",
]
OSNAP_TRANSPORT_FILES = ["OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc"]

# Mapping of filenames to download URLs
OSNAP_FILE_URLS = {
    "README_OSNAP-MOC_202306.doc": "https://repository.gatech.edu/bitstreams/930261ff-6cca-4cf9-81c8-d27c51a4ca49/download",
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/e039e311-dd2e-4511-a525-c2fcfb3be85a/download",
    "OSNAP_Streamfunction_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/5edf4cba-a28f-40a6-a4da-24d7436a42ab/download",
    "OSNAP_Gridded_TSV_201408_202006_2023.nc": "https://repository.gatech.edu/bitstreams/598f200a-50ba-4af0-96af-bd29fe692cdc/download",
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
    "OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc": {
        "data_product": "Time series of MOC, MHT, and MFT",
    },
    "OSNAP_Streamfunction_201408_202006_2023.nc": {
        "data_product": "Meridional overturning streamfunction",
    },
    "OSNAP_Gridded_TSV_201408_202006_2023.nc": {
        "data_product": "Gridded temperature, salinity, and velocity",
    },
}


@apply_defaults(None, OSNAP_DEFAULT_FILES)
def read_osnap(
    source: str,
    file_list: Union[str, list[str]],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the OSNAP transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to OSNAP_DEFAULT_FILES.
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

    Raises
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read OSNAP dataset")

    # Ensure file_list has a default
    if file_list is None:
        file_list = OSNAP_DEFAULT_FILES
    if transport_only:
        file_list = OSNAP_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    datasets = []

    for file in file_list:
        if not file.lower().endswith(".nc"):
            log.warning("Skipping non-NetCDF file: %s", file)
            continue

        download_url = OSNAP_FILE_URLS.get(file)
        if not download_url:
            log.error("No download URL defined for OSNAP file: %s", file)
            raise FileNotFoundError(f"No download URL defined for OSNAP file {file}")

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # Open dataset
        try:
            log.info("Opening OSNAP dataset: %s", file_path)
            ds = xr.open_dataset(file_path)
        except Exception as e:
            log.error("Failed to open NetCDF file: %s: %s", file_path, e)
            raise FileNotFoundError(f"Failed to open NetCDF file: {file_path}: {e}")

        # Attach metadata
        file_metadata = OSNAP_FILE_METADATA.get(file, {})
        log.info("Attaching metadata to dataset from file: %s", file)
        utilities.safe_update_attrs(
            ds,
            {
                "source_file": file,
                "source_path": str(file_path),
                **OSNAP_METADATA,
                **file_metadata,
            },
        )

        datasets.append(ds)

    if not datasets:
        log.error("No valid NetCDF files found in %s", file_list)
        raise FileNotFoundError(f"No valid NetCDF files found in {file_list}")

    log.info("Successfully loaded %d OSNAP dataset(s)", len(datasets))

    return datasets
