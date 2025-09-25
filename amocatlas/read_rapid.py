from pathlib import Path
from typing import Union

import xarray as xr

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Default list of RAPID data files
RAPID_DEFAULT_SOURCE = "https://rapid.ac.uk/sites/default/files/rapid_data/"
RAPID_TRANSPORT_FILES = ["moc_transports.nc"]
RAPID_DEFAULT_FILES = [
    "moc_transports.nc",
    "moc_vertical.nc",
    "ts_gridded.nc",
    "2d_gridded.nc",
    "meridional_transports.nc",
]

# Inline metadata dictionary
RAPID_METADATA = {
    "description": "RAPID 26N transport estimates dataset",
    "project": "RAPID-AMOC 26°N array",
    "web_link": "https://rapid.ac.uk/rapidmoc",
    "note": "Dataset accessed and processed via xarray",
}

# File-specific metadata placeholder
RAPID_FILE_METADATA = {
    "moc_transports.nc": {
        "data_product": "RAPID layer transport time series",
    },
    "moc_vertical.nc": {
        "data_product": "RAPID vertical streamfunction time series",
    },
    "ts_gridded.nc": {
        "data_product": "RAPID gridded temperature and salinity",
    },
    "2d_gridded.nc": {
        "data_product": "RAPID 2D gridded temperature and salinity",
    },
    "meridional_transports.nc": {
        "data_product": "RAPID meridional transport time series",
    },
}
# https://rapid.ac.uk/sites/default/files/rapid_data/ts_gridded.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/moc_vertical.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/moc_transports.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/2d_gridded.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/meridional_transports.nc


@apply_defaults(RAPID_DEFAULT_SOURCE, RAPID_DEFAULT_FILES)
def read_rapid(
    source: Union[str, Path, None],
    file_list: Union[str, list[str]],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the RAPID transport dataset from a URL or local file path into an xarray.Dataset.

    Parameters
    ----------
    source : str, optional
        URL or local path to the NetCDF file(s).
        Defaults to the RAPID data repository URL.
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        If None, will attempt to list files in the source directory.
    transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional
        If True, force redownload of the data.

    Returns
    -------
    xr.Dataset
        The loaded xarray dataset with basic inline metadata.

    Raises
    ------
    ValueError
        If the source is neither a valid URL nor a directory path.
    FileNotFoundError
        If no valid NetCDF files are found in the provided file list.

    """
    log_info("Starting to read RAPID dataset")

    if file_list is None:
        file_list = RAPID_DEFAULT_FILES
    if transport_only:
        file_list = RAPID_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    datasets = []

    for file in file_list:
        if not file.lower().endswith(".nc"):
            log_warning("Skipping non-NetCDF file: %s", file)
            continue

        download_url = (
            f"{source.rstrip('/')}/{file}" if utilities._is_valid_url(source) else None
        )

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        try:
            log_info("Opening RAPID dataset: %s", file_path)
            ds = xr.open_dataset(file_path)
        except Exception as e:
            log_error("Failed to open NetCDF file: %s: %s", file_path, e)
            raise FileNotFoundError(f"Failed to open NetCDF file: {file_path}: {e}")

        file_metadata = RAPID_FILE_METADATA.get(file, {})
        log_info("Attaching metadata to RAPID dataset from file: %s", file)
        utilities.safe_update_attrs(
            ds,
            {
                "source_file": file,
                "source_path": str(file_path),
                **RAPID_METADATA,
                **file_metadata,
            },
        )

        datasets.append(ds)

    if not datasets:
        log_error("No valid RAPID NetCDF files found in %s", file_list)
        raise FileNotFoundError(f"No valid RAPID NetCDF files found in {file_list}")

    log_info("Successfully loaded %d RAPID dataset(s)", len(datasets))

    return datasets
