"""Intuitive namespace API for AMOCatlas data readers.

This module provides a more user-friendly API for accessing AMOC array data
with discoverable function names and consistent return types. Each array gets
its own function with IDE autocompletion support.

Key improvements over readers.load_dataset():
- Single dataset returned by default (most common use case)
- all_files=True parameter for power users who need multiple files
- Array-specific parameters feel natural (e.g., version for OSNAP)
- IDE autocompletion works for array names

Examples
--------
Basic usage (single dataset):
    >>> from amocatlas import read
    >>> data = read.rapid()                    # Single transport dataset
    >>> osnap = read.osnap(version="2025")     # Latest OSNAP data
    >>> arctic = read.arcticgateway()          # Arctic gateway transports

Power user access (multiple datasets):
    >>> all_rapid = read.rapid(all_files=True)     # List of all RAPID files
    >>> all_osnap = read.osnap(all_files=True)      # List of all OSNAP files

Custom parameters:
    >>> rapid_custom = read.rapid(
    ...     source="https://my-mirror.com/rapid/",
    ...     transport_only=False,
    ...     redownload=True
    ... )

"""

from collections.abc import Callable
from pathlib import Path

import xarray as xr

# Import standardization functions
from . import standardise

# Import all the individual readers from the data_sources package
from .data_sources import (
    read_41n,
    read_47n,
    read_arcticgateway,
    read_axmoc22s,
    read_axmoc34s,
    read_calafat2025,
    read_dso,
    read_fbc,
    read_fw2015,
    read_lebras35n,
    read_mocha,
    read_move,
    read_nac,
    read_osnap,
    read_ovide,
    read_rapid,
    read_samba,
    read_scotia,
    read_sf2021,
    read_zheng2024,
)
from .data_sources.arcticgateway import ARCTIC_DEFAULT_FILES
from .data_sources.axmoc22s import AXMOC22S_DEFAULT_FILES
from .data_sources.axmoc34s import AXMOC34S_DEFAULT_FILES
from .data_sources.calafat2025 import CALAFAT2025_DEFAULT_FILES
from .data_sources.dso import DSO_DEFAULT_FILES
from .data_sources.fbc import FBC_DEFAULT_FILES
from .data_sources.fw2015 import FW2015_DEFAULT_FILES
from .data_sources.lebras35n import LEBRAS35N_DEFAULT_FILES
from .data_sources.mocha26n import MOCHA_DEFAULT_FILES
from .data_sources.move16n import MOVE_DEFAULT_FILES
from .data_sources.nac import NAC_DEFAULT_FILES
from .data_sources.noac47n import NOAC47N_DEFAULT_FILES
from .data_sources.osnap55n import OSNAP_DEFAULT_FILES
from .data_sources.ovide import OVIDE_DEFAULT_FILES

# Import file constants for list_files() functionality
from .data_sources.rapid26n import RAPID_DEFAULT_FILES
from .data_sources.samba34s import SAMBA_DEFAULT_FILES
from .data_sources.scotia import SCOTIA_DEFAULT_FILES
from .data_sources.sf2021 import SF2021_DEFAULT_FILES
from .data_sources.wh41n import WH41N_DEFAULT_FILES
from .data_sources.zheng2024 import ZHENG2024_DEFAULT_FILES

# Supported datasource IDs for standardization
SUPPORTED_STANDARDIZATION = {
    "rapid26n",
    "move16n",
    "osnap55n",
    "samba34s",
    "arcticgateway",
    "fw2015",
    "mocha26n",
    "wh41n",
    "dso",
    "noac47n",
    "fbc",
    "calafat2025",
    "zheng2024",
    "nac",
    "sf2021",
    "lebras35n",
    "axmoc22s",
    "axmoc34s",
    "ovide",
    "scotia",
}


def _return_single_or_list(
    datasets: list[xr.Dataset],
    all_files: bool,
    file_list: str | list[str] | None = None,
) -> xr.Dataset | list[xr.Dataset]:
    """Helper function to return single dataset or list based on user's request.

    Parameters
    ----------
    datasets : list of xr.Dataset
        List of loaded datasets.
    all_files : bool
        If True, return the list.
    file_list : str, list of str, or None
        The file list provided by user (to determine intent).

    Returns
    -------
    xr.Dataset or list of xr.Dataset
        - Single dataset if user requested single file
        - List of datasets if user requested multiple files or all_files=True

    Raises
    ------
    ValueError
        If no datasets were loaded.

    """
    if not datasets:
        raise ValueError("No datasets were loaded")

    # Return list if explicitly requested via all_files=True
    if all_files:
        return datasets

    # Return list if user provided multiple files in file_list
    if file_list is not None:
        file_list_normalized = file_list if isinstance(file_list, list) else [file_list]
        if len(file_list_normalized) > 1:
            return datasets

    # Otherwise return single dataset (default behavior)
    return datasets[0]


def _validate_file_selection_params(
    transport_only: bool,
    all_files: bool,
    file_list: str | list[str] | None,
    available_files: list[str],
    transport_files: list[str] = None,  # noqa: ARG001
) -> tuple[bool, str | list[str] | None]:
    """Validate and resolve file selection parameters.

    Parameters
    ----------
    transport_only : bool
        Whether to use only transport files
    all_files : bool
        Whether to use all available files
    file_list : str, list of str, or None
        Custom list of files to use
    available_files : list of str
        All available files for this array
    transport_files : list of str, optional
        Transport-only files for this array

    Returns
    -------
    tuple[bool, Union[str, List[str], None]]
        (effective_transport_only, effective_file_list)

    Raises
    ------
    ValueError
        If conflicting parameters are provided

    """
    # Count explicitly provided parameters (excluding defaults)
    # Note: We need to distinguish between default transport_only=True and explicitly set transport_only=True
    # For now, we'll be permissive and let file_list override transport_only default
    provided_params = []
    if all_files:
        provided_params.append("all_files=True")
    if file_list is not None:
        provided_params.append("file_list")

    # Check for conflicting combinations
    if len(provided_params) > 1:
        if "all_files=True" in provided_params and "file_list" in provided_params:
            # Check if file_list matches all available files (order doesn't matter)
            file_list_normalized = (
                file_list if isinstance(file_list, list) else [file_list]
            )
            if set(file_list_normalized) != set(available_files):
                raise ValueError(
                    f"all_files=True conflicts with file_list. "
                    f"Expected all files {available_files}, got {file_list_normalized}"
                )

    # Resolve effective parameters
    if all_files:
        return False, None  # Use all files, transport_only=False
    if file_list is not None:
        return False, file_list  # Use custom file list, transport_only=False
    return transport_only, None  # Use defaults


def _create_array_function(
    reader_func: Callable,
    array_name: str,
    supports_version: bool = False,
    available_files: list[str] = None,
) -> Callable:
    """Create a uniform API function for an array reader with optional standardization.

    This factory function eliminates repetition by generating the standard
    interface for each array reader automatically. By default, applies standardization
    for clean, analysis-ready data unless raw=True is specified.

    Parameters
    ----------
    reader_func : callable
        The underlying reader function (e.g., read_rapid)
    array_name : str
        Name of the array (for documentation)
    supports_version : bool, optional
        Whether this reader supports the version parameter
    available_files : list of str, optional
        List of available files for this array
    standardize_func : callable, optional
        Standardization function to apply (e.g., standardise.standardise_rapid)

    Returns
    -------
    callable
        A function with uniform signature that wraps the reader

    """

    def array_function(
        source: str | Path | None = None,
        file_list: str | list[str] | None = None,
        transport_only: bool = True,
        all_files: bool = False,
        raw: bool = False,
        data_dir: str | Path | None = None,
        redownload: bool = False,
        version: str = None,
        track_added_attrs: bool = False,
    ) -> xr.Dataset | list[xr.Dataset]:
        # TODO: Get transport files for validation - this needs to be implemented properly
        transport_files = None  # We'll need to map this based on reader_func

        # Validate and resolve file selection parameters
        effective_transport_only, effective_file_list = _validate_file_selection_params(
            transport_only=transport_only,
            all_files=all_files,
            file_list=file_list,
            available_files=available_files
            or [],  # Available files passed from factory
            transport_files=transport_files,
        )

        kwargs = {
            "source": source,
            "file_list": effective_file_list,
            "transport_only": effective_transport_only,
            "data_dir": data_dir,
            "redownload": redownload,
            "track_added_attrs": track_added_attrs,
        }

        # Only pass version if the reader supports it
        if supports_version and version is not None:
            kwargs["version"] = version

        # Load raw datasets
        reader_result = reader_func(**kwargs)

        # Handle the case where track_added_attrs=True returns a tuple
        if track_added_attrs:
            datasets, added_attrs_per_dataset = reader_result
            # Embed metadata changes into each dataset's attributes
            for i, ds in enumerate(datasets):
                if i < len(added_attrs_per_dataset):
                    ds.attrs["_amocatlas_metadata_changes"] = added_attrs_per_dataset[i]
                else:
                    ds.attrs["_amocatlas_metadata_changes"] = {
                        "added": [],
                        "modified": [],
                    }
        else:
            datasets = reader_result

        # Apply standardization by default (unless raw=True)
        if not raw:
            try:
                # Apply standardization to each dataset based on its datasource_id
                standardized_datasets = []
                for i, ds in enumerate(datasets):
                    # Get datasource_id from dataset metadata
                    datasource_id = ds.attrs.get("processing_datasource")

                    if datasource_id and datasource_id in SUPPORTED_STANDARDIZATION:
                        # Get file name for standardization (needed by standardize functions)
                        if isinstance(file_list, list) and i < len(file_list):
                            file_name = file_list[i]
                        elif isinstance(file_list, str):
                            file_name = file_list
                        else:
                            # Use source_file from metadata or default
                            file_name = ds.attrs.get(
                                "source_file", f"{array_name.lower()}_data.nc"
                            )

                        standardized_ds = standardise.standardise_data(ds, file_name)
                        standardized_datasets.append(standardized_ds)
                    else:
                        # No standardization available, keep raw data
                        standardized_datasets.append(ds)

                datasets = standardized_datasets

            except (ValueError, KeyError, TypeError, AttributeError) as e:
                # If standardization fails, log warning but continue with raw data
                import warnings

                # Print a visible warning message
                print(f"!! WARNING: Standardization failed for {array_name}: {e}")
                print("!! Returning raw data instead of standardized data.")

                warnings.warn(
                    f"Standardization failed for {array_name}: {e}. Returning raw data.",
                    UserWarning,
                    stacklevel=2,
                )

        # Return datasets (metadata changes are now embedded in dataset attributes)
        return _return_single_or_list(datasets, all_files, file_list)

    # Add proper docstring
    array_function.__doc__ = f"""Load {array_name} array data.

    By default, returns standardized, analysis-ready data with consistent variable names,
    metadata, and units following oceanographic conventions. Use raw=True to get data
    in original format from the source files.

    Parameters
    ----------
    source : str, Path, or None, optional
        URL or local path to the data source.
    file_list : str, list of str, or None, optional
        Specific files to load. Defaults to transport files.
    transport_only : bool, optional
        If True, load only transport data. Default: True.
    all_files : bool, optional
        If True, return list of all datasets. If False, return single dataset. Default: False.
    raw : bool, optional
        If True, return data in original format without standardization.
        If False (default), apply standardization for analysis-ready data.
    data_dir : str, Path, or None, optional
        Local directory for data storage.
    redownload : bool, optional
        Force redownload of data. Default: False.
    version : str, optional
        Dataset version{" (used for version selection)" if supports_version else " (ignored for this array)"}. Default: None.
    track_added_attrs : bool, optional
        **INTERNAL USE ONLY** - Track which attributes were added during metadata
        enrichment. When True, embeds a temporary '_amocatlas_metadata_changes'
        attribute in each returned dataset containing {{"added": [...], "modified": [...]}}.
        This attribute should be extracted and removed by calling code (e.g., report
        generation). Not intended for end users. Default: False.
    Returns
    -------
    xr.Dataset or list of xr.Dataset
        Standardized dataset (default) or raw dataset if raw=True.
        Single dataset by default, or list of datasets if all_files=True.
    Notes
    -----
    Standardization includes:
    - Consistent variable names across arrays
    - Proper CF-compliant metadata and attributes
    - Standardized units following oceanographic conventions
    - Additional quality control and formatting
    """

    # Add list_files() method to the function
    def list_files() -> list[str]:
        """Return list of available files for this array.

        Returns
        -------
        list of str
            List of available file names that can be specified in file_list parameter.

        """
        return available_files.copy() if available_files else []

    array_function.list_files = list_files
    return array_function


# Create all array functions using the factory pattern with automatic standardization
rapid = _create_array_function(
    read_rapid, "RAPID 26°N", available_files=RAPID_DEFAULT_FILES
)
move = _create_array_function(
    read_move, "MOVE 16°N", available_files=MOVE_DEFAULT_FILES
)
osnap = _create_array_function(
    read_osnap, "OSNAP", supports_version=True, available_files=OSNAP_DEFAULT_FILES
)
samba = _create_array_function(
    read_samba, "SAMBA 34.5°S", available_files=SAMBA_DEFAULT_FILES
)
arcticgateway = _create_array_function(
    read_arcticgateway, "Arctic Gateway", available_files=ARCTIC_DEFAULT_FILES
)
fw2015 = _create_array_function(
    read_fw2015, "Frajka-Williams 2015", available_files=FW2015_DEFAULT_FILES
)
mocha = _create_array_function(read_mocha, "MOCHA", available_files=MOCHA_DEFAULT_FILES)
wh41n = _create_array_function(read_41n, "41°N", available_files=WH41N_DEFAULT_FILES)
dso = _create_array_function(
    read_dso, "Denmark Strait Overflow", available_files=DSO_DEFAULT_FILES
)
noac47n = _create_array_function(
    read_47n, "47°N", available_files=NOAC47N_DEFAULT_FILES
)
fbc = _create_array_function(
    read_fbc, "Faroe Bank Channel", available_files=FBC_DEFAULT_FILES
)
calafat2025 = _create_array_function(
    read_calafat2025, "Calafat et al. 2025", available_files=CALAFAT2025_DEFAULT_FILES
)
zheng2024 = _create_array_function(
    read_zheng2024, "Zheng et al. 2024", available_files=ZHENG2024_DEFAULT_FILES
)
nac = _create_array_function(
    read_nac, "North Atlantic Current", available_files=NAC_DEFAULT_FILES
)
sf2021 = _create_array_function(
    read_sf2021, "Sanchez-Franks et al. 2021", available_files=SF2021_DEFAULT_FILES
)
lebras35n = _create_array_function(
    read_lebras35n,
    "Le Bras et al. 2023 at 35°N",
    available_files=LEBRAS35N_DEFAULT_FILES,
)
axmoc22s = _create_array_function(
    read_axmoc22s,
    "AXMOC 22.5°S",
    available_files=AXMOC22S_DEFAULT_FILES,
)
axmoc34s = _create_array_function(
    read_axmoc34s,
    "AXMOC 34.5°S",
    available_files=AXMOC34S_DEFAULT_FILES,
)
ovide = _create_array_function(
    read_ovide,
    "OVIDE",
    available_files=OVIDE_DEFAULT_FILES,
)
scotia = _create_array_function(
    read_scotia,
    "SCOTIA",
    available_files=SCOTIA_DEFAULT_FILES,
)

# Define __all__ to control what's exported
__all__ = [
    "rapid",
    "move",
    "osnap",
    "samba",
    "arcticgateway",
    "fw2015",
    "mocha",
    "wh41n",
    "dso",
    "noac47n",
    "fbc",
    "calafat2025",
    "zheng2024",
    "nac",
    "sf2021",
    "lebras35n",
    "axmoc22s",
    "axmoc34s",
    "ovide",
    "scotia",
]
