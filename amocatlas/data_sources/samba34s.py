"""SAMBA array data reader for AMOCatlas.

This module provides functions to read and process data from the SAMBA
(South Atlantic Meridional Overturning Circulation) observing array
located at 34.5°S.
"""

from pathlib import Path

import pandas as pd
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_debug, log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults, sanitize_variable_name

log = logger.log  # Use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "samba34s"

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
    "Upper_Abyssal_Transport_Anomalies.txt": "ftp://ftp.aoml.noaa.gov/phod/pub/SAM/2020_Kersale_etal_ScienceAdvances/Upper_Abyssal_Transport_Anomalies.txt",
    "MOC_TotalAnomaly_and_constituents.asc": "https://www.aoml.noaa.gov/phod/SAMOC_international/documents/MOC_TotalAnomaly_and_constituents.asc",
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
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
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
    track_added_attrs : bool, optional
        If True, track which attributes were added during metadata enrichment.

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

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, SAMBA_METADATA
    )

    # Ensure file_list has a default
    if file_list is None:
        file_list = SAMBA_DEFAULT_FILES
    if transport_only:
        file_list = SAMBA_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = ReaderUtils.setup_data_directory(data_dir)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, SAMBA_FILE_METADATA)

    datasets = []
    added_attrs_per_dataset = [] if track_added_attrs else None

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

            # Sanitize column names to create valid Python identifiers
            # This handles cases like "Total MOC anomaly (relative to record-length average of 14.7 Sv)"
            sanitized_column_names = [
                sanitize_variable_name(name) for name in column_names
            ]
            df.columns = sanitized_column_names

            # Store original column names mapping for later use in variable mapping
            # This enables tracking of original names -> sanitized names -> standardized names
            original_to_sanitized = dict(
                zip(column_names, sanitized_column_names, strict=False)
            )
        except (
            OSError,
            ValueError,
            KeyError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            log_error("Failed to parse ASCII file: %s: %s", file_path, e)
            raise FileNotFoundError(
                f"Failed to parse ASCII file: {file_path}: {e}"
            ) from e

        # Time handling - use sanitized column names
        # Find the sanitized versions of time columns
        time_cols_needed = ["Year", "Month", "Day", "Hour"]
        if "Upper_Abyssal" in file:
            time_cols_needed.append("Minute")

        # Map original time column names to their sanitized versions
        sanitized_time_cols = []
        missing_cols = []
        for col in time_cols_needed:
            if col in original_to_sanitized:
                sanitized_time_cols.append(original_to_sanitized[col])
            elif col in df.columns:
                sanitized_time_cols.append(col)  # Fallback if already sanitized
            else:
                missing_cols.append(col)

        if missing_cols:
            raise KeyError(f"Required time columns {missing_cols} not found in data")

        try:
            if "Upper_Abyssal" in file:
                df["TIME"] = pd.to_datetime(df[sanitized_time_cols])
            else:
                df["TIME"] = pd.to_datetime(
                    df[sanitized_time_cols[:4]]
                )  # Year, Month, Day, Hour only

            df = df.drop(columns=sanitized_time_cols)
        except (ValueError, KeyError, TypeError) as e:
            log_error("Failed to construct TIME column for %s: %s", file, e)
            raise ValueError(f"Failed to construct TIME column for {file}: {e}") from e

        # Convert DataFrame to xarray Dataset
        try:
            ds = df.set_index("TIME").to_xarray()
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            log_error(
                "Failed to convert DataFrame to xarray Dataset for %s: %s",
                file,
                e,
            )
            raise ValueError(
                f"Failed to convert DataFrame to xarray Dataset for {file}: {e}",
            ) from e

        # Attach metadata with optional tracking
        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                SAMBA_FILE_METADATA,
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
                SAMBA_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        # Update variable_mapping to use sanitized names as keys
        # This allows standardization to find the mapping from sanitized names to standard names
        if "variable_mapping" in ds.attrs:
            original_mapping = ds.attrs["variable_mapping"].copy()
            updated_mapping = {}

            for original_name, standard_name in original_mapping.items():
                # Find the sanitized version of this original name
                sanitized_name = original_to_sanitized.get(original_name)
                if sanitized_name and sanitized_name in ds.data_vars:
                    updated_mapping[sanitized_name] = standard_name
                    log_debug(
                        f"Updated variable mapping: {original_name} -> {sanitized_name} -> {standard_name}"
                    )
                else:
                    # Keep original mapping in case sanitization didn't change it
                    updated_mapping[original_name] = standard_name

            ds.attrs["variable_mapping"] = updated_mapping

            # Store the full mapping chain for reference (useful for reports)
            ds.attrs["original_variable_mapping"] = original_mapping
            ds.attrs["sanitization_mapping"] = original_to_sanitized

        datasets.append(ds)

    # Use ReaderUtils for validation
    ReaderUtils.validate_datasets_loaded(datasets, file_list)

    # Handle track_added_attrs parameter
    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
