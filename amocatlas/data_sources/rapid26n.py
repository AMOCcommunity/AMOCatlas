"""RAPID array data reader for AMOCatlas.

This module provides functions to read and process data from the RAPID
(Rapid Climate Change) observing array located at 26°N in the Atlantic.

"""

from pathlib import Path

import xarray as xr

# Import the modules used
from amocatlas import logger, utilities
from amocatlas.logger import log_info
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log  # Use the global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "rapid26n"

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
        "data_product": "Layer transports - individual water mass transport components (thermocline, intermediate water, NADW, AABW, Ekman, Florida Straits)",
    },
    "moc_vertical.nc": {
        "data_product": "Vertical streamfunction - overturning circulation streamfunction as function of depth and time",
    },
    "ts_gridded.nc": {
        "data_product": "Gridded temperature and salinity - T/S profiles from moorings across the basin",
    },
    "2d_gridded.nc": {
        "data_product": "Monthly velocity and hydrography fields - Conservative Temperature (CT), Absolute Salinity (SA), and velocities on regular grid",
    },
    "meridional_transports.nc": {
        "data_product": "Heat and freshwater transports - AMOC strength, heat transport, freshwater transport, and overturning streamfunctions in density space",
    },
}
# https://rapid.ac.uk/sites/default/files/rapid_data/ts_gridded.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/moc_vertical.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/moc_transports.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/2d_gridded.nc
# https://rapid.ac.uk/sites/default/files/rapid_data/meridional_transports.nc


@apply_defaults(RAPID_DEFAULT_SOURCE, RAPID_DEFAULT_FILES)
def read_rapid(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset] | tuple[list[xr.Dataset], list[list[str]]]:
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
    track_added_attrs : bool, optional
        If True, return tuple of (datasets, list_of_metadata_changes_per_dataset).
        If False, return only datasets. Default is False.

    Returns
    -------
    list[xr.Dataset] or tuple[list[xr.Dataset], list[dict]]
        If track_added_attrs=False: List of loaded datasets with metadata.
        If track_added_attrs=True: Tuple of (datasets, list of metadata changes per dataset).

    Raises
    ------
    ValueError
        If the source is neither a valid URL nor a directory path.
    FileNotFoundError
        If no valid NetCDF files are found in the provided file list.

    """
    log_info("Starting to read RAPID dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, RAPID_METADATA
    )

    # Use ReaderUtils for common operations
    file_list = ReaderUtils.prepare_file_list(
        file_list, RAPID_DEFAULT_FILES, RAPID_TRANSPORT_FILES, transport_only
    )
    local_data_dir = ReaderUtils.setup_data_directory(data_dir)

    # Print information about files being loaded - use YAML metadata if available
    netcdf_files = ReaderUtils.filter_netcdf_files(file_list)
    display_file_metadata = (
        yaml_file_metadata if yaml_file_metadata else RAPID_FILE_METADATA
    )
    ReaderUtils.print_loading_info(netcdf_files, DATASOURCE_ID, display_file_metadata)

    datasets = []
    added_attrs_per_dataset = []

    for file in netcdf_files:
        # RAPID-specific URL construction
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

        # Use ReaderUtils for consistent dataset loading and metadata
        ds = ReaderUtils.safe_load_dataset(file_path)

        # Fix sigma0 and sigma2 coordinates for meridional_transports.nc
        # These values come in as potential density (e.g., 1027) but should be
        # potential density anomaly (e.g., 27)
        if file == "meridional_transports.nc":
            if "sigma0" in ds.coords:
                original_values = ds["sigma0"].values
                if (
                    original_values.max() > 100
                ):  # Check if values are in absolute density range (>1000) rather than anomaly range
                    log_info(
                        f"Fixing sigma0 coordinates in {file}: subtracting 1000 to get density anomaly"
                    )
                    # Preserve existing attributes from the DataArray
                    original_attrs = ds["sigma0"].attrs.copy()
                    ds["sigma0"] = ds["sigma0"] - 1000
                    # Restore the preserved attributes
                    ds["sigma0"].attrs.update(original_attrs)

            if "sigma2" in ds.coords:
                original_values = ds["sigma2"].values
                if (
                    original_values.max() > 100
                ):  # Check if values are in absolute density range (>1000) rather than anomaly range
                    log_info(
                        f"Fixing sigma2 coordinates in {file}: subtracting 1000 to get density anomaly"
                    )
                    # Preserve existing attributes from the DataArray
                    original_attrs = ds["sigma2"].attrs.copy()
                    ds["sigma2"] = ds["sigma2"] - 1000
                    # Restore the preserved attributes
                    ds["sigma2"].attrs.update(original_attrs)

        # Get file-specific metadata from YAML or fallback to hardcoded
        if file in yaml_file_metadata:
            file_metadata = yaml_file_metadata[file]
        else:
            file_metadata = RAPID_FILE_METADATA.get(file, {})

        # Apply variable mapping and coordinate metadata from YAML
        if file in yaml_file_metadata and yaml_file_metadata[file]:
            yaml_file_data = yaml_file_metadata[file]

            # Variable mapping will be handled in standardization stage (Option A approach)
            # Store mapping for later use but don't apply renaming here
            var_mapping = yaml_file_data.get("variable_mapping", {})

            # Apply coordinate metadata from YAML
            # Since we're not renaming in reader, use original coordinate names
            coord_metadata = yaml_file_data.get("coordinates", {})
            for coord_name, coord_attrs in coord_metadata.items():
                if coord_name in ds.coords:
                    ds[coord_name].attrs.update(coord_attrs)

            # Apply variable metadata from YAML using original variable names
            # (standardized names will get metadata applied during standardization)
            var_metadata = yaml_file_data.get("variables", {})
            for std_var_name, var_attrs in var_metadata.items():
                # Find the original variable name that maps to this standardized name
                orig_var_name = None
                for orig, std in var_mapping.items():
                    if std == std_var_name:
                        orig_var_name = orig
                        break

                # Apply metadata to original variable name if it exists in dataset
                if orig_var_name and orig_var_name in ds.data_vars:
                    ds[orig_var_name].attrs.update(var_attrs)

        if track_added_attrs:
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

    # Use ReaderUtils for validation
    ReaderUtils.validate_datasets_loaded(datasets, file_list)

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
