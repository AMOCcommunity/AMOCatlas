"""AMOCatlas data readers: unified interface for AMOC observing arrays.

This module provides the main interface for loading data from multiple
Atlantic Meridional Overturning Circulation (AMOC) observing arrays.
It serves as the orchestrator that routes requests to specific array
readers and provides both sample and full dataset loading capabilities.

The module supports data from:
- RAPID (26°N)
- MOVE (16°N)
- OSNAP (Subpolar North Atlantic)
- SAMBA (34.5°S)
- MOCHA, 41°N, DSO, and FW2015 arrays

Main functions:
- load_dataset(): Load full datasets from any supported array
- load_sample_dataset(): Load small sample datasets for testing
"""

import warnings
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import xarray as xr

from amocatlas import logger
from amocatlas.data_sources import (
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
    read_osnap_2025,
    read_rapid,
    read_samba,
    read_sf2021,
    read_zheng2024,
)
from amocatlas.logger import log_info

log = logger.log

# Dropbox location Public/linked_elsewhere/amocatlas_data/
server = "https://www.dropbox.com/scl/fo/4bjo8slq1krn5rkhbkyds/AM-EVfSHi8ro7u2y8WAcKyw?rlkey=16nqlykhgkwfyfeodkj274xpc&dl=0"


def _get_reader(array_name: str) -> Callable[..., list[xr.Dataset]]:
    """Return the reader function for the given array name.

    Parameters
    ----------
    array_name : str
        The name of the observing array.

    Returns
    -------
    function
        Reader function corresponding to the given array name.

    Raises
    ------
    ValueError
        If an unknown array name is provided.

    """
    readers = {
        "move": read_move,
        "rapid": read_rapid,
        "osnap": read_osnap,
        "osnap_2025": read_osnap_2025,
        "samba": read_samba,
        "fw2015": read_fw2015,
        "mocha": read_mocha,
        "41n": read_41n,
        "dso": read_dso,
        "calafat2025": read_calafat2025,
        "zheng2024": read_zheng2024,
        "47n": read_47n,
        "fbc": read_fbc,
        "arcticgateway": read_arcticgateway,
        "nac": read_nac,
        "sf2021": read_sf2021,
        "lebras35n": read_lebras35n,
        "axmoc22s": read_axmoc22s,
        "axmoc34s": read_axmoc34s,
    }
    try:
        return readers[array_name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown array name: {array_name}. Valid options are: {list(readers.keys())}",
        ) from None


def load_sample_dataset(array_name: str = "rapid") -> xr.Dataset:
    """Load a sample dataset for quick testing.

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        Use the new intuitive API instead: :mod:`amocatlas.read` (e.g., ``amocatlas.read.rapid()``).

    Currently supports:
    - 'rapid' : loads the 'RAPID_26N_TRANSPORT.nc' file

    Parameters
    ----------
    array_name : str, optional
        The name of the observing array to load. Default is 'rapid'.

    Returns
    -------
    xr.Dataset
        A single xarray Dataset from the sample file.

    Raises
    ------
    ValueError
        If the array_name is not recognised.

    """
    warnings.warn(
        "load_sample_dataset() is deprecated and will be removed in a future version. "
        "Use the new intuitive API instead: amocatlas.read.rapid()",
        DeprecationWarning,
        stacklevel=2,
    )

    if array_name.lower() == "rapid":
        sample_file = "moc_transports.nc"
        datasets = load_dataset(
            array_name=array_name,
            file_list=sample_file,
            transport_only=True,
        )
        if not datasets:
            raise FileNotFoundError(
                f"No datasets were loaded for sample file: {sample_file}",
            )
        return datasets[0]

    raise ValueError(
        f"Sample dataset for array '{array_name}' is not defined. "
        "Currently only 'rapid' is supported.",
    )


def load_dataset(
    array_name: str,
    source: str = None,
    file_list: str | list[str] = None,
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
) -> list[xr.Dataset]:
    """Load raw datasets from a selected AMOC observing array.

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        Use the new intuitive API instead: :mod:`amocatlas.read` (e.g., ``amocatlas.read.rapid()``).

    Parameters
    ----------
    array_name : str
        The name of the observing array to load. Options are:
        - 'move' : MOVE 16N array
        - 'rapid' : RAPID 26N array
        - 'osnap' : OSNAP array (2014-2022, configurable version via main reader)
        - 'osnap_2025' : OSNAP array (2014-2022, dedicated 2025 reader function)
        - 'samba' : SAMBA 34S array
        - 'fw2015' : FW2015 array
        - '41n' : 41N array
        - 'dso' : DSO array
        - 'calafat2025' : CALAFAT2025 array
        - 'zheng2024' : ZHENG2024 array
        - '47n' : 47N array
        - 'fbc' : Faroe Bank Channel overflow array
        - 'arcticgateway' : ARCTIC Gateway array
        - 'nac' : North Atlantic Current array
        - 'sf2021' : SF2021 array
        - 'lebras35n' : LEBRAS 35N array
    source : str, optional
        URL or local path to the data source.
        If None, the reader-specific default source will be used.
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        If None, the reader-specific default files will be used.
    transport_only : bool, optional
        If True, restrict to transport files only.
    data_dir : str, optional
        Local directory for downloaded files.
    redownload : bool, optional
        If True, force redownload of the data.

    Returns
    -------
    list of xarray.Dataset
        List of datasets loaded from the specified array.

    Raises
    ------
    ValueError
        If an unknown array name is provided.

    """
    warnings.warn(
        "load_dataset() is deprecated and will be removed in a future version. "
        f"Use the new intuitive API instead: amocatlas.read.{array_name.lower()}()",
        DeprecationWarning,
        stacklevel=2,
    )

    if logger.LOGGING_ENABLED:
        logger.setup_logger(array_name=array_name)

    # Use logger globally
    log_info(f"Loading dataset for array: {array_name}")

    reader = _get_reader(array_name)
    datasets = reader(
        source=source,
        file_list=file_list,
        transport_only=transport_only,
        data_dir=data_dir,
        redownload=redownload,
    )

    log_info(f"Successfully loaded {len(datasets)} dataset(s) for array: {array_name}")
    _summarise_datasets(datasets, array_name)

    return datasets


def _summarise_datasets(datasets: list, array_name: str) -> None:
    """Print and log a summary of loaded datasets."""
    summary_lines = []
    summary_lines.append(f"Summary for array '{array_name}':")
    summary_lines.append(f"Total datasets loaded: {len(datasets)}\n")

    for idx, ds in enumerate(datasets, start=1):
        summary_lines.append(f"Dataset {idx}:")

        # Filename from metadata
        source_file = ds.attrs.get("source_file", "Unknown")
        summary_lines.append(f"  Source file: {source_file}")

        # Time coverage
        time_var = ds.get("TIME")
        if time_var is not None:
            time_clean = pd.to_datetime(time_var.values)
            time_clean = time_clean[~pd.isna(time_clean)]

            if len(time_clean) > 0:
                time_start = time_clean[0].strftime("%Y-%m-%d")
                time_end = time_clean[-1].strftime("%Y-%m-%d")
                summary_lines.append(f"  Time coverage: {time_start} to {time_end}")
            else:
                summary_lines.append("  Time coverage: no valid time values found")

        # Dimensions
        summary_lines.append("  Dimensions:")
        for dim, size in ds.sizes.items():
            summary_lines.append(f"    - {dim}: {size}")

        # Variables
        summary_lines.append("  Variables:")
        for var in ds.data_vars:
            shape = ds[var].shape
            summary_lines.append(f"    - {var}: shape {shape}")

        summary_lines.append("")  # empty line between datasets

    summary = "\n".join(summary_lines)

    # Print to console
    print(summary)

    # Write to log
    log_info("\n" + summary)
