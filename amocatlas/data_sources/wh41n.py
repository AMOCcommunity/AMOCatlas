"""41°N array data reader for AMOCatlas.

This module provides functions to read and process data from the 41°N
observing array in the North Atlantic. This array monitors the Atlantic
Meridional Overturning Circulation and associated heat transport at the
northern boundary of the subtropical gyre.
"""

from pathlib import Path
from typing import Union

import xarray as xr
import datetime
import pandas
from pandas.errors import EmptyDataError, ParserError

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.utilities import apply_defaults
from amocatlas.reader_utils import ReaderUtils

log = logger.log  # Use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "wh41n"

# Default list of 41N data files
WH41N_DEFAULT_FILES = [
    "hobbs_willis_amoc41N_tseries.txt",
    "trans_ARGO_ERA5.nc",
    "Q_ARGO_obs_dens_2000depth_ERA5.nc",
]
A41N_TRANSPORT_FILES = ["hobbs_willis_amoc41N_tseries.txt"]
A41N_DEFAULT_SOURCE = "https://zenodo.org/records/18238115/files/"

A41N_METADATA = {
    "project": "Atlantic Meridional Overturning Circulation Near 41N from Altimetry and Argo Observations",
    "weblink": "https://zenodo.org/records/18238115",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
    "doi": "10.5281/zenodo.8170365",
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


@apply_defaults(A41N_DEFAULT_SOURCE, WH41N_DEFAULT_FILES)
def read_41n(
    ##    source: str,
    source: Union[str, Path, None],
    file_list: Union[str, list[str]],
    transport_only: bool = True,
    data_dir: Union[str, Path, None] = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the 41N transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to 41N_DEFAULT_FILES.
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
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read 41N dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, A41N_METADATA
    )

    # Ensure file_list has a default
    if file_list is None:
        file_list = WH41N_DEFAULT_FILES
    if transport_only:
        file_list = A41N_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]
    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, A41N_FILE_METADATA)

    datasets = []

    added_attrs_per_dataset = [] if track_added_attrs else None
    for file in file_list:
        if not (file.lower().endswith(".txt") or file.lower().endswith(".nc")):
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
            # file .nc
            # Use ReaderUtils for consistent dataset loading
            ds = ReaderUtils.safe_load_dataset(file_path)

            # Fix time coordinate for ARGO files: convert YYYYMM to datetime
            if ("trans_ARGO_ERA5" in file or "Q_ARGO" in file) and "time" in ds.coords:
                time_data = ds["time"]
                if hasattr(
                    time_data.values, "dtype"
                ) and time_data.values.dtype.kind in ["i", "u"]:
                    # Check if values look like YYYYMM format
                    first_val = int(time_data.values[0])
                    if 200000 <= first_val <= 250000:  # YYYYMM range check
                        log_info(
                            f"Converting YYYYMM time format to datetime for {file}"
                        )

                        # Convert YYYYMM to datetime
                        yyyymm_values = time_data.values
                        datetime_values = []
                        for yyyymm in yyyymm_values:
                            year = yyyymm // 100
                            month = yyyymm % 100
                            # Use 15th of month as representative date
                            dt = pandas.Timestamp(year=year, month=month, day=15)
                            datetime_values.append(dt)

                        # Replace time coordinate with TIME and convert to standard format
                        ds = ds.rename({"time": "TIME"})
                        ds = ds.assign_coords(TIME=datetime_values)

                        # Add proper TIME coordinate attributes
                        ds["TIME"].attrs.update(
                            {
                                "long_name": "Time",
                                "standard_name": "time",
                                "calendar": "gregorian",
                                "units": "datetime64[ns]",
                            }
                        )
        else:
            # file .txt - handle both old format (with % comments) and new CSV format
            try:
                column_names, _ = utilities.parse_ascii_header(
                    file_path, comment_char="%"
                )
                df = utilities.read_ascii_file(file_path, comment_char="%")

                if column_names:
                    # Old format with % comment headers - use parsed column names
                    df.columns = column_names
                else:
                    # New CSV format (v5) - file starts directly with header line
                    # Re-read as proper CSV to get correct column parsing
                    df = pandas.read_csv(file_path)
                    # Ensure we have the expected 5 columns
                    expected_columns = [
                        "Decimal year",
                        "Ekman (Sv)",
                        "Geos (Sv)",
                        "MOC (Sv)",
                        "MOC (PW)",
                    ]
                    if len(df.columns) == len(expected_columns):
                        df.columns = expected_columns
                    else:
                        log_error(
                            "Unexpected number of columns (%d) in CSV file %s",
                            len(df.columns),
                            file,
                        )
                        # Use expected columns anyway as fallback
                        df.columns = expected_columns[: len(df.columns)]
            except (
                OSError,
                IOError,
                ValueError,
                KeyError,
                EmptyDataError,
                ParserError,
            ) as e:
                log_error("Failed to parse ASCII file: %s: %s", file_path, e)
                raise FileNotFoundError(
                    f"Failed to parse ASCII file: {file_path}: {e}"
                ) from e
            # Time handling
            try:
                df = df.apply(
                    lambda col: (
                        col.astype(str).str.replace(",", "", regex=False).astype(float)
                    )
                )
                # df['Decimal year'] = df['Decimal year'].astype(str).str.replace(',', '',regex=False).astype(float)
                df["TIME"] = df["Decimal year"].apply(
                    lambda x: (
                        datetime.datetime(int(x), 1, 1)
                        + datetime.timedelta(
                            days=(x - int(x))
                            * (
                                datetime.datetime(int(x) + 1, 1, 1)
                                - datetime.datetime(int(x), 1, 1)
                            ).days
                        )
                    )
                )
                df = df.drop(columns=["Decimal year"])
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

        # Use ReaderUtils for consistent metadata attachment (for all file types)
        file_metadata = yaml_file_metadata.get(file, A41N_FILE_METADATA.get(file, {}))
        if track_added_attrs:
            # Attach metadata with tracking
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                file_metadata,
                DATASOURCE_ID,
                track_added_attrs=True,
            )
            added_attrs_per_dataset.append(attr_changes)
        else:
            # Standard metadata attachment without tracking
            ds = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                file_metadata,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid 41N files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d 41N dataset(s)", len(datasets))
    # Handle track_added_attrs parameter

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    else:
        return datasets
