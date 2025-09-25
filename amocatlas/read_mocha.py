from pathlib import Path
from typing import Union
import zipfile
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.utilities import apply_defaults

log = logger.log  # ✅ use the global logger

# Default source and file list
MOCHA_DEFAULT_SOURCE = "https://scholarship.miami.edu/view/fileRedirect?instCode=01UOML_INST&filePid=13426966980002976&download=true"
MOCHA_DEFAULT_FILES = ["Johns_2023_mht_data_2020_ERA5.zip"]
MOCHA_TRANSPORT_FILES = ["Johns_2023_mht_data_2020_ERA5.zip"]
MOCHA_ZIP_CONTENTS = {
    "Johns_2023_mht_data_2020_ERA5.zip": {
        "mocha_mht_data_ERA5_v2020.nc",
        "mocha_mht_data_ERA5_v2020.mat",
        "README_2020_ERA5.pdf",
        "README.txt",
    }
}

# Mapping of filenames to download URLs
MOCHA_FILE_URLS = {
    "Johns_2023_mht_data_2020_ERA5.zip": (
        "https://scholarship.miami.edu/view/fileRedirect?instCode=01UOML_INST&filePid=13426966980002976&download=true"
    ),
}

# Global metadata for MOCHA
MOCHA_METADATA = {
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

# File-specific metadata placeholder
MOCHA_FILE_METADATA = {
    "mocha_mht_data_ERA5_v2020.nc": {
        "data_product": "MOCHA heat transport time series",
        "project": "RAPID-MOCHA",
        # Add specific acknowledgments here if needed in future
    },
}


@apply_defaults(None, MOCHA_DEFAULT_FILES)
def read_mocha(
    source: str,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the MOCHA transport dataset from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        URL or local path to the NetCDF file(s).
        Defaults to the MOCHA data repository URL.
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to MOCHA_DEFAULT_FILES.
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
        If the source is neither a valid URL nor a directory path.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read MOCHA dataset")

    if file_list is None:
        file_list = MOCHA_DEFAULT_FILES
    if transport_only:
        file_list = MOCHA_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    datasets = []

    for file in file_list:
        download_url = MOCHA_FILE_URLS.get(file)
        if not download_url:
            log.error("No download URL found for file: %s", file)
            raise ValueError(f"No download URL found for file: {file}")

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # If the file is a zip, extract all contents
        file_path = Path(file_path)
        if file_path.suffix == ".zip":
            contents = MOCHA_ZIP_CONTENTS.get(file)
            if not contents:
                raise ValueError(
                    f"No internal file mapping provided for zip file: {file}"
                )

            with zipfile.ZipFile(file_path, "r") as zip_ref:
                for member in contents:
                    target_path = local_data_dir / member
                    if redownload or not target_path.exists():
                        log.info("Extracting %s from %s", member, file)
                        zip_ref.extract(member, path=local_data_dir)

            # Look specifically for the .nc file to open
            nc_files = [f for f in contents if f.endswith(".nc")]
            if not nc_files:
                raise FileNotFoundError(
                    f"No NetCDF (.nc) file listed in zip contents for {file}"
                )

            for nc_file in nc_files:
                nc_path = local_data_dir / nc_file
                if not nc_path.exists():
                    raise FileNotFoundError(
                        f"Expected NetCDF file not found: {nc_path}"
                    )

                log.info("Opening MOCHA dataset: %s", nc_path)
                try:
                    ds = xr.open_dataset(nc_path)
                except Exception as e:
                    log.error("Failed to open NetCDF file: %s: %s", nc_path, e)
                    raise FileNotFoundError(
                        f"Failed to open NetCDF file: {nc_path}: {e}"
                    )

                metadata = MOCHA_FILE_METADATA.get(nc_file, {})
                utilities.safe_update_attrs(
                    ds,
                    {
                        "source_file": nc_file,
                        "source_path": str(nc_path),
                        **MOCHA_METADATA,
                        **metadata,
                    },
                )

                datasets.append(ds)
        else:
            log.warning("Non-zip MOCHA files are not currently supported: %s", file)

    if not datasets:
        log.error("No valid NetCDF files found in %s", file_list)
        raise FileNotFoundError(f"No valid NetCDF files found in {file_list}")

    log.info("Successfully loaded %d MOCHA dataset(s)", len(datasets))
    return datasets
