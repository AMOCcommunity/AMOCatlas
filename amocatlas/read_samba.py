from pathlib import Path
from typing import Union

import pandas as pd
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Default file list
SAMBA_DEFAULT_FILES = [
    "Upper_Abyssal_Transport_Anomalies.txt",
    "MOC_TotalAnomaly_and_constituents.asc",
]
SAMBA_TRANSPORT_FILES = [
    "Upper_Abyssal_Transport_Anomalies.txt",
    "MOC_TotalAnomaly_and_constituents.asc",
]
# Mapping of filenames to remote URLs
SAMBA_FILE_URLS = {
    "Upper_Abyssal_Transport_Anomalies.txt": "ftp://ftp.aoml.noaa.gov/phod/pub/SAM/2020_Kersale_etal_ScienceAdvances/",
    "MOC_TotalAnomaly_and_constituents.asc": "https://www.aoml.noaa.gov/phod/SAMOC_international/documents/",
}

# Global metadata for SAMBA
SAMBA_METADATA = {
    "description": "SAMBA 34S transport estimates dataset",
    "project": "South Atlantic MOC Basin-wide Array (SAMBA)",
    "weblink": "https://www.aoml.noaa.gov/phod/SAMOC_international/",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
    "acknowledgement": "SAMBA data were collected and made freely available by the SAMOC international project and contributing national programs.",
    # Add DOI here when available
}

# File-specific metadata placeholders
SAMBA_FILE_METADATA = {
    "Upper_Abyssal_Transport_Anomalies.txt": {
        "data_product": "Daily volume transport anomaly estimates for the upper and abyssal cells of the MOC",
        "acknowledgement": "M. Kersalé et al., Highly variable upper and abyssal overturning cells in the South Atlantic. Sci. Adv. 6, eaba7573 (2020). DOI: 10.1126/sciadv.aba7573",
    },
    "MOC_TotalAnomaly_and_constituents.asc": {
        "data_product": "Daily travel time values, calibrated to a nominal pressure of 1000 dbar, and bottom pressures from the two PIES/CPIES moorings",
        "acknowledgement": "Meinen, C. S., Speich, S., Piola, A. R., Ansorge, I., Campos, E., Kersalé, M., et al. (2018). Meridional overturning circulation transport variability at 34.5°S during 2009–2017: Baroclinic and barotropic flows and the dueling influence of the boundaries. Geophysical Research Letters, 45, 4180–4188. https://doi.org/10.1029/2018GL077408",
    },
}


@apply_defaults(None, SAMBA_DEFAULT_FILES)
def read_samba(
    source: Union[str, Path, None],
    file_list: Union[str, list[str]],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load the SAMBA transport datasets from remote URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        URL or local path to the dataset directory. If None, will use predefined URLs per file.
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to SAMBA_DEFAULT_FILES.
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
        If no source is provided for a file and no default URL mapping found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log_info("Starting to read SAMBA dataset")

    # Ensure file_list has a default
    if file_list is None:
        file_list = SAMBA_DEFAULT_FILES
    if transport_only:
        file_list = SAMBA_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    datasets = []

    for file in file_list:
        if not (file.lower().endswith(".txt") or file.lower().endswith(".asc")):
            log_warning("Skipping unsupported file type: %s", file)
            continue

        download_url = SAMBA_FILE_URLS.get(file)
        if not download_url:
            log_error("No download URL defined for SAMBA file: %s", file)
            raise FileNotFoundError(f"No download URL defined for SAMBA file {file}")

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # Parse ASCII file
        try:
            column_names, _ = utilities.parse_ascii_header(file_path, comment_char="%")
            df = utilities.read_ascii_file(file_path, comment_char="%")
            df.columns = column_names
        except Exception as e:
            log_error("Failed to parse ASCII file: %s: %s", file_path, e)
            raise FileNotFoundError(f"Failed to parse ASCII file: {file_path}: {e}")

        # Time handling
        try:
            if "Upper_Abyssal" in file:
                df["TIME"] = pd.to_datetime(
                    df[["Year", "Month", "Day", "Hour", "Minute"]],
                )
                df = df.drop(columns=["Year", "Month", "Day", "Hour", "Minute"])
            else:
                df["TIME"] = pd.to_datetime(df[["Year", "Month", "Day", "Hour"]])
                df = df.drop(columns=["Year", "Month", "Day", "Hour"])
        except Exception as e:
            log_error("Failed to construct TIME column for %s: %s", file, e)
            raise ValueError(f"Failed to construct TIME column for {file}: {e}")

        # Convert DataFrame to xarray Dataset
        try:
            ds = df.set_index("TIME").to_xarray()
        except Exception as e:
            log_error(
                "Failed to convert DataFrame to xarray Dataset for %s: %s",
                file,
                e,
            )
            raise ValueError(
                f"Failed to convert DataFrame to xarray Dataset for {file}: {e}",
            )

        # Attach metadata
        file_metadata = SAMBA_FILE_METADATA.get(file, {})
        log_info("Attaching metadata to SAMBA dataset from file: %s", file)
        utilities.safe_update_attrs(
            ds,
            {
                "source_file": file,
                "source_path": str(file_path),
                **SAMBA_METADATA,
                **file_metadata,
            },
        )

        datasets.append(ds)

    if not datasets:
        log_error("No valid SAMBA files found in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d SAMBA dataset(s)", len(datasets))
    return datasets
