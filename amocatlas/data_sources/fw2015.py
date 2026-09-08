"""Frajka-Williams 2015 dataset reader for AMOCatlas.

This module provides functions to read and process data from the
Frajka-Williams et al. (2015) AMOC proxy dataset. This dataset provides
a reconstruction of AMOC variability based on sea surface height and wind
stress observations, extending the observational record beyond direct
mooring observations.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log  # Use global logger

# Datasource identifier for automatic standardization
DATASOURCE_ID = "fw2015"

# Default file list
FW2015_DEFAULT_FILES = [
    "MOCproxy_for_figshare_v1.0.mat",
]
FW2015_TRANSPORT_FILES = ["MOCproxy_for_figshare_v1.0.mat"]

# Mapping of filenames to download URLs
FW2015_FILE_URLS = {
    "README.txt": "https://zenodo.org/records/18606051/files/README%20for%20MOCproxy_for_figshare.txt",
    "MOCproxy_for_figshare_v1.0.mat": "https://zenodo.org/records/18606051/files/MOCproxy_for_figshare_v1.0.mat",
}

# General Metadata (global for FW2015)

FW2015_METADATA = {
    "project": "Estimating the Atlantic overturning at 26°N using satellite altimetry and cable measurements",
    "doi": "10.5281/zenodo.18606051",
}


# File-specific metadata (placeholder, ready to extend)
FW2015_FILE_METADATA = {
    "MOCproxy_for_figshare_v1.0.mat": {
        "data_product": "Time series of MOC",
    },
}


@apply_defaults(None, FW2015_DEFAULT_FILES)
def read_fw2015(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the FW2015 transport datasets from a URL or local file path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process.
        Defaults to FW2015_DEFAULT_FILES.
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
    log_info("Starting to read FW2015 dataset")

    # Load YAML metadata with fallback
    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, FW2015_METADATA
    )

    # ensure file_list has a default
    if file_list is None:
        file_list = FW2015_DEFAULT_FILES
    if transport_only:
        file_list = FW2015_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    # Determine the local storage path
    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    # Print information about files being loaded
    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, FW2015_FILE_METADATA)

    datasets = []

    added_attrs_per_dataset = [] if track_added_attrs else None
    for file in file_list:
        if not (file.lower().endswith(".txt") or file.lower().endswith(".mat")):
            log_warning("Skipping unsupported file type: %s", file)
            continue

        download_url = FW2015_FILE_URLS.get(file)
        if not download_url:
            log_error("No download URL defined for FW2015 file: %s", file)
            raise FileNotFoundError(f"No download URL defined for FW2015 file {file}")

        file_path = utilities.resolve_file_path(
            file_name=file,
            source=source,
            download_url=download_url,
            local_data_dir=local_data_dir,
            redownload=redownload,
        )

        # open dataset

        try:
            log.info("Opening fw2015 file: %s", file_path)
            mat_data = scipy.io.loadmat(
                file_path, squeeze_me=True, struct_as_record=False
            )
            recon = mat_data.get("recon")
            mocgrid = mat_data.get("mocgrid")

            time = recon.time  # time in decimal years

            # Use original MATLAB field names (renaming will happen in standardization)
            # Note: time is used as coordinate, not as a data variable
            variables = {
                "mocproxy": recon.mocproxy,
                "ek": recon.ek,
                "h1umo": recon.h1umo,  # Original name, will be renamed to SSHA in standardization
                "gs": recon.gs,
                "umoproxy": recon.umoproxy,
                "moc": mocgrid.moc,  # Grid variables use original names too
                "ek_grid": mocgrid.ek,  # Use lowercase with underscore for consistency
                "gs_grid": mocgrid.gs,
                "lnadw": mocgrid.lnadw,
                "umo": mocgrid.umo,
                "unadw": mocgrid.unadw,
            }

            # Convert decimal years to datetime
            time = np.asarray(time)
            time = pd.to_datetime(
                (time - 719529).astype("int"), origin="unix", unit="D"
            )

            # Build dataset
            ds = xr.Dataset(
                {
                    name: ("time", np.asarray(values))
                    for name, values in variables.items()
                },
                coords={"time": time},
            )

            # add global attributes
            ds.attrs["created"] = recon.created
            ds.attrs["url"] = recon.url
            ds.attrs["paper"] = recon.paper
            ds.attrs["version"] = recon.version

        except (OSError, ValueError, KeyError, AttributeError) as e:
            log.exception("Failed to parse .mat file: %s", file_path)
            raise ValueError(f"Failed to parse .mat file: {file_path}: {e}") from e

        # attach metadata
        # Attach metadata with optional tracking

        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                FW2015_FILE_METADATA,
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
                FW2015_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    if not datasets:
        log.error("No valid FW2015 files found in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log.info("Successfully loaded %d FW2015 dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
