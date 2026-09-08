"""SCOTIA overturning reader for AMOCatlas.

Reads the monthly overturning diagnostics of the Scotland-Canada overturning array
(SCOTIA; Fox et al. 2026), computed in neutral-density (gamma-n) space across the
subpolar North Atlantic. The upstream product has two files on a SAMS THREDDS server:
a small diagnostics time series (served here) and a large gridded T/S/velocity field
(~2 GB, not downloaded). Only the diagnostics file is read by default.

The diagnostics carry the overturning streamfunction ``psi`` and the transport-by-class
``transport`` on a neutral-density coordinate ``gamma_n_bin``, the streamfunction maximum
``moc`` and the density ``gamma_moc`` at which it occurs, plus northward heat (``hf``),
freshwater (``ff``) and density (``df``) fluxes. Raw variable names are kept so the
metadata ``variable_mapping`` can rename them downstream.
"""

from pathlib import Path

import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_debug, log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log

DATASOURCE_ID = "scotia"

# Only the diagnostics file is served; the companion SCOTIA_gridded.nc is ~2 GB and is
# left on the THREDDS server (reachable via OPeNDAP subsetting) rather than downloaded.
SCOTIA_DEFAULT_FILES = ["SCOTIA_overturning_diagnostics.nc"]
SCOTIA_TRANSPORT_FILES = ["SCOTIA_overturning_diagnostics.nc"]
SCOTIA_DEFAULT_SOURCE = "https://thredds.sams.ac.uk/thredds/fileServer/Fox_et_al_2026/"

SCOTIA_METADATA = {
    "project": "SCOTIA",
    "weblink": "https://thredds.sams.ac.uk/thredds/catalog/Fox_et_al_2026/catalog.html",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

SCOTIA_FILE_METADATA = {
    "SCOTIA_overturning_diagnostics.nc": {
        "data_product": "Monthly overturning diagnostics of the Scotland-Canada overturning array in neutral-density space",
    }
}

# Bin-bound coordinates dropped in v1 (see _drop_gamma_bounds).
_GAMMA_BOUND_VARS = ("gamma_n_lower", "gamma_n_upper")


def _drop_gamma_bounds(ds: xr.Dataset, source_file: str = None) -> xr.Dataset:
    """Drop the neutral-density bin-bound arrays from the SCOTIA diagnostics.

    The file carries ``gamma_n_lower``/``gamma_n_upper`` (the lower/upper edges of each
    neutral-density bin) alongside the bin centres ``gamma_n_bin``. Rather than risk a
    dangling CF ``bounds`` reference surviving the downstream rename, v1 serves only the
    bin centres; the drop is logged, not silent, and the bounds can be reconstructed from
    the source if needed.

    Parameters
    ----------
    ds : xr.Dataset
        Raw SCOTIA diagnostics dataset.
    source_file : str, optional
        Source filename, for provenance in log messages.

    Returns
    -------
    xr.Dataset
        Dataset with the two bin-bound coordinates removed (if present).

    """
    file_context = f" ({source_file})" if source_file else ""
    present = [v for v in _GAMMA_BOUND_VARS if v in ds.variables]
    if present:
        ds = ds.drop_vars(present)
        log_info(
            "Dropped SCOTIA neutral-density bin-bound arrays %s%s; serving bin centres only",
            present,
            file_context,
        )
    else:
        log_debug(f"No SCOTIA bin-bound arrays to drop{file_context}")
    return ds


@apply_defaults(SCOTIA_DEFAULT_SOURCE, SCOTIA_DEFAULT_FILES)
def read_scotia(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the SCOTIA overturning diagnostics from a URL or local path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path or base URL to the data directory (remote source handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process. Defaults to SCOTIA_DEFAULT_FILES.
    transport_only : bool, optional
        If True, restrict to transport (diagnostics) files only.
    data_dir : str, Path or None, optional
        Optional local data directory.
    redownload : bool, optional
        If True, force redownload of the data.
    track_added_attrs : bool, optional
        If True, track which attributes were added during metadata enrichment.

    Returns
    -------
    list of xr.Dataset
        List with the single SCOTIA diagnostics dataset, metadata attached.

    Raises
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read SCOTIA dataset")

    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, SCOTIA_METADATA
    )

    if file_list is None:
        file_list = SCOTIA_DEFAULT_FILES
    if transport_only:
        file_list = SCOTIA_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, SCOTIA_FILE_METADATA)

    datasets = []
    added_attrs_per_dataset = [] if track_added_attrs else None

    for file in file_list:
        if not file.lower().endswith(".nc"):
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

        ds = ReaderUtils.safe_load_dataset(file_path)
        ds = _drop_gamma_bounds(ds, source_file=file)

        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                SCOTIA_FILE_METADATA,
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
                SCOTIA_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid SCOTIA files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d SCOTIA dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
