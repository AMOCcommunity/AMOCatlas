"""OVIDE MOC-intensity reader for AMOCatlas.

Reads the monthly MOC-intensity time series across the Greenland-Portugal A25 OVIDE line
(Mercier et al., SEANOE 10.17882/46445). The file carries two indices on different time
bases: ``MOC_index_ISAS`` (2002-2015; altimetry surface combined with the time-varying
Argo/ISAS interior) and ``MOC_index_AVISO`` (1993-2015; altimetry combined with a fixed
2002-2015 mean ISAS interior -- an altimetry proxy), plus ``err_index_ISAS`` (the ISAS
ensemble standard deviation). The two monthly timestamp grids coincide exactly, so all three
are served on a single 1993-2015 TIME axis, with the ISAS series NaN before 2002.
"""

from pathlib import Path

import pandas as pd
import xarray as xr

from amocatlas import logger, utilities
from amocatlas.logger import log_debug, log_error, log_info, log_warning
from amocatlas.reader_utils import ReaderUtils
from amocatlas.utilities import apply_defaults

log = logger.log

DATASOURCE_ID = "ovide"

OVIDE_DEFAULT_FILES = ["46195.nc"]
OVIDE_TRANSPORT_FILES = ["46195.nc"]
OVIDE_DEFAULT_SOURCE = "https://www.seanoe.org/data/00353/46445/data/"

OVIDE_METADATA = {
    "project": "OVIDE",
    "weblink": "https://www.seanoe.org/data/00353/46445/",
    "comment": "Dataset accessed and processed via http://github.com/AMOCcommunity/amocatlas",
}

OVIDE_FILE_METADATA = {
    "46195.nc": {
        "data_product": "Monthly MOC-intensity time series across the Greenland-Portugal A25 OVIDE line",
    }
}

_TIME_METADATA = {
    "units": "seconds since 1970-01-01T00:00:00Z",
    "long_name": "Time elapsed since 1970-01-01T00:00:00Z",
    "standard_name": "time",
    "calendar": "gregorian",
    "vocabulary": "http://vocab.nerc.ac.uk/collection/OG1/current/TIME/",
}

# Epochs taken from the file's own coordinate descriptions.
_AVISO_EPOCH = "1993-01-15"
_ISAS_EPOCH = "2002-01-15"


def _merge_ovide_time_axes(ds: xr.Dataset, source_file: str = None) -> xr.Dataset:
    """Merge the two OVIDE indices onto a single monthly TIME axis.

    ``date_AVISO`` (days since 1993-01-15) and ``date_ISAS`` (days since 2002-01-15) are both
    monthly and their timestamps coincide, so the ISAS variables are reindexed onto the AVISO
    axis (NaN before 2002). Raw variable names are kept so the metadata ``variable_mapping``
    can rename them downstream.

    Parameters
    ----------
    ds : xr.Dataset
        Raw OVIDE dataset with ``date_AVISO`` and ``date_ISAS`` dimensions.
    source_file : str, optional
        Source filename, for provenance in log messages.

    Returns
    -------
    xr.Dataset
        Dataset on a single datetime ``date_AVISO`` axis carrying ``MOC_index_AVISO``,
        ``MOC_index_ISAS`` and ``err_index_ISAS``.

    """
    file_context = f" ({source_file})" if source_file else ""
    if "date_AVISO" not in ds.dims or "date_ISAS" not in ds.dims:
        log_debug(
            f"OVIDE merge skipped{file_context}: expected date_AVISO/date_ISAS dims"
        )
        return ds

    aviso_time = pd.Timestamp(_AVISO_EPOCH) + pd.to_timedelta(
        ds["date_AVISO"].values, unit="D"
    )
    isas_time = pd.Timestamp(_ISAS_EPOCH) + pd.to_timedelta(
        ds["date_ISAS"].values, unit="D"
    )

    aviso = ds[["MOC_index_AVISO"]].assign_coords(date_AVISO=aviso_time.values)
    isas = (
        ds[["MOC_index_ISAS", "err_index_ISAS"]]
        .assign_coords(date_ISAS=isas_time.values)
        .rename(date_ISAS="date_AVISO")
        .reindex(date_AVISO=aviso_time.values)
    )
    merged = xr.merge([aviso, isas])

    for var in ("MOC_index_AVISO", "MOC_index_ISAS", "err_index_ISAS"):
        merged[var].attrs = dict(ds[var].attrs)
    merged["date_AVISO"].attrs = _TIME_METADATA
    merged.attrs = dict(ds.attrs)
    log_debug(f"Merged OVIDE indices onto a single TIME axis{file_context}")
    return merged


@apply_defaults(OVIDE_DEFAULT_SOURCE, OVIDE_DEFAULT_FILES)
def read_ovide(
    source: str | Path | None,
    file_list: str | list[str],
    transport_only: bool = True,
    data_dir: str | Path | None = None,
    redownload: bool = False,
    track_added_attrs: bool = False,
) -> list[xr.Dataset]:
    """Load the OVIDE MOC-intensity dataset from a URL or local path into xarray Datasets.

    Parameters
    ----------
    source : str, optional
        Local path to the data directory (remote source is handled per-file).
    file_list : str or list of str, optional
        Filename or list of filenames to process. Defaults to OVIDE_DEFAULT_FILES.
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
        List with the single OVIDE dataset, metadata attached and both indices on one TIME axis.

    Raises
    ------
    ValueError
        If no source is provided for a file and no default URL mapping is found.
    FileNotFoundError
        If the file cannot be downloaded or does not exist locally.

    """
    log.info("Starting to read OVIDE dataset")

    global_metadata, yaml_file_metadata = ReaderUtils.load_array_metadata_with_fallback(
        DATASOURCE_ID, OVIDE_METADATA
    )

    if file_list is None:
        file_list = OVIDE_DEFAULT_FILES
    if transport_only:
        file_list = OVIDE_TRANSPORT_FILES
    if isinstance(file_list, str):
        file_list = [file_list]

    local_data_dir = Path(data_dir) if data_dir else utilities.get_default_data_dir()
    local_data_dir.mkdir(parents=True, exist_ok=True)

    ReaderUtils.print_loading_info(file_list, DATASOURCE_ID, OVIDE_FILE_METADATA)

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
        # Collapse the two time axes onto one before attaching metadata.
        ds = _merge_ovide_time_axes(ds, source_file=file)

        if track_added_attrs:
            ds, attr_changes = ReaderUtils.attach_metadata_with_tracking(
                ds,
                file,
                file_path,
                global_metadata,
                yaml_file_metadata,
                OVIDE_FILE_METADATA,
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
                OVIDE_FILE_METADATA,
                DATASOURCE_ID,
                track_added_attrs=False,
            )

        datasets.append(ds)

    if not datasets:
        log_error("No valid OVIDE files in %s", file_list)
        raise FileNotFoundError(f"No valid data files found in {file_list}")

    log_info("Successfully loaded %d OVIDE dataset(s)", len(datasets))

    if track_added_attrs:
        return datasets, added_attrs_per_dataset
    return datasets
