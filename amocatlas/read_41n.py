from pathlib import Path
from typing import Union

import xarray as xr
import datetime

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Default list of 41N data files
A41N_DEFAULT_FILES = [
    "hobbs_willis_amoc41N_tseries.txt",
    "trans_ARGO_ERA5.nc",
    "Q_ARGO_obs_dens_2000depth_ERA5.nc",
]
A41N_TRANSPORT_FILES = ["hobbs_willis_amoc41N_tseries.txt"]
A41N_DEFAULT_SOURCE = "https://zenodo.org/records/14681441/files/"

A41N_METADATA = {
    "project": "Atlantic Meridional Overturning Circulation Near 41N from Altimetry and Argo Observations",
    "weblink": "https://zenodo.org/records/14681441",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
    "acknowledgement": "This study has been conducted using E.U. Copernicus Marine Service Information; https://doi.org/10.48670/moi-00149  and https://doi.org/10.48670/moi-00148. These data were collected and made freely available by the International Argo Program and the national programs that contribute to it.  (https://argo.ucsd.edu,  https://www.ocean-ops.org). The Argo Program is part of the Global Ocean Observing System.",
    "doi": "10.5281/zenodo.8170365",
    "paper": "Willis, J. K., and Hobbs, W. R., Atlantic Meridional Overturning Circulation Near 41N from Altimetry and Argo Observations. Dataset access [2025-05-27] at 10.5281/zenodo.8170366.",
}

A41N_FILE_METADATA = {
    "hobbs_willis_amoc41N_tseries.txt": {
        "data_product": "Transport time series of Ekman volume, Northward geostrophc, Meridional Overturning volume and Meridional Overturning Heat",
    },
    "trans_Argo_ERA5.nc": {
        "data_product": "Time series of geostrophic transport as a function of latitude, longitude, depth and time, for the upper 2000 m for latitudes near 41 N and time series of Ekman Transport and Overturning Transport",
    },
    "Q_ARGO_obs_dens_2000depth_ERA5.nc": {
        "data_product": "Time series of heat transport based on various assumptions about the temperature of the ocean for depths below 2000m",
    },
}


@apply_defaults(A41N_DEFAULT_SOURCE, A41N_DEFAULT_FILES)
def read_41n(
    ##    source: str,
    source: Union[str, Path, None],
    file_list: Union[str, list[str]],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the 41N transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------                                                      source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to 41N_DEFAULT_FILES.                            transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional                                         If True, force redownload of the data.

    Returns
    -------
    list of xr.Dataset
        List of loaded xarray datasets with basic inline and file-specific metadata.

    Raises
    ------                                                          ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError                                                   If the file cannot be downloaded or does not exist locally.
    """
    log.info("Starting to read 41N dataset")  # Ensure file_list has a default
    if file_list is None:
        file_list = A41N_DEFAULT_FILES
    if transport_only:
        file_list = A41N_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]
    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    datasets = []

    for file in file_list:
        if not (file.lower().endswith(".txt") or file.lower().endswith(".nc")):
            log_warning("Skipping unsupported file type : %s", file)
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

        # Open dataset

        if file.lower().endswith(".nc"):
            # file .nc
            try:
                log.info("Opening 41N dataset: %s", file_path)
                ds = xr.open_dataset(file_path)
            except Exception as e:
                log.error("Failed to open NetCDF file: %s: %s", file_path, e)
                raise FileNotFoundError(
                    f"Failed to open NetCDF file : {file_path}: {e}"
                )
        else:
            # file .txt
            try:
                column_names, _ = utilities.parse_ascii_header(
                    file_path, comment_char="%"
                )
                df = utilities.read_ascii_file(file_path, comment_char="%")
                df.columns = column_names
            except Exception as e:
                log_error("Failed to parse ASCII file: %s: %s", file_path, e)
                raise FileNotFoundError(f"Failed to parse ASCII file: {file_path}: {e}")
            # Time handling
            try:
                df = df.apply(
                    lambda col: col.astype(str)
                    .str.replace(",", "", regex=False)
                    .astype(float)
                )
                # df['Decimal year'] = df['Decimal year'].astype(str).str.replace(',', '',regex=False).astype(float)
                df["TIME"] = df["Decimal year"].apply(
                    lambda x: datetime.datetime(int(x), 1, 1)
                    + datetime.timedelta(
                        days=(x - int(x))
                        * (
                            datetime.datetime(int(x) + 1, 1, 1)
                            - datetime.datetime(int(x), 1, 1)
                        ).days
                    )
                )
                df = df.drop(columns=["Decimal year"])
                ds = df.set_index("TIME").to_xarray()
            except Exception as e:
                log_error(
                    "Failed to convert DataFrame to xarray Fataset for %s: %s",
                    file,
                    e,
                )
                raise ValueError(
                    f"Failed to convert DataFrame to xarray Dataset for {file}: {e}",
                )
            # Attach metadata
            file_metadata = A41N_FILE_METADATA.get(file, {})
            log_info("Attaching metadata to 41N dataset from file: %s", file)
            utilities.safe_update_attrs(
                ds,
                {
                    "source_file": file,
                    "source_path": str(file_path),
                    **A41N_METADATA,
                    **file_metadata,
                },
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid 41N files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Succesfully loaded %d 41N dataset(s)", len(datasets))
    return datasets
