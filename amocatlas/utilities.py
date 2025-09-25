from ftplib import FTP
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
import yaml
import re


import pandas as pd
import requests
import xarray as xr

from amocatlas import logger
from amocatlas.logger import log_debug

log = logger.log
from importlib import resources


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent


def get_default_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def apply_defaults(default_source: str, default_files: List[str]) -> Callable:
    """Decorator to apply default values for 'source' and 'file_list' parameters if they are None.

    Parameters
    ----------
    default_source : str
        Default source URL or path.
    default_files : list of str
        Default list of filenames.

    Returns
    -------
    Callable
        A wrapped function with defaults applied.

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            source: Optional[str] = None,
            file_list: Optional[List[str]] = None,
            *args,
            **kwargs,
        ) -> Callable:
            if source is None:
                source = default_source
            if file_list is None:
                file_list = default_files
            return func(source=source, file_list=file_list, *args, **kwargs)

        return wrapper

    return decorator


def normalize_whitespace(attrs: dict) -> dict:
    """
    Replace non-breaking & other unusual whitespace in every string attr value
    with a normal ASCII space, and collapse runs of whitespace down to one space.
    """
    ws_pattern = re.compile(r"\s+")
    cleaned = {}
    for k, v in attrs.items():
        if isinstance(v, str):
            # 1) replace non-breaking spaces with normal spaces
            t = v.replace("\u00A0", " ")
            # 2) collapse any runs of whitespace (tabs, newlines, NBSP, etc.) to a single space
            t = ws_pattern.sub(" ", t).strip()
            cleaned[k] = t
        else:
            cleaned[k] = v
    return cleaned


def resolve_file_path(
    file_name: str,
    source: Union[str, Path, None],
    download_url: Optional[str],
    local_data_dir: Path,
    redownload: bool = False,
) -> Path:
    """Resolve the path to a data file, using local source, cache, or downloading if necessary.

    Parameters
    ----------
    file_name : str
        The name of the file to resolve.
    source : str or Path or None
        Optional local source directory.
    download_url : str or None
        URL to download the file if needed.
    local_data_dir : Path
        Directory where downloaded files are stored.
    redownload : bool, optional
        If True, force redownload even if cached file exists.

    Returns
    -------
    Path
        Path to the resolved file.

    """
    # Use local source if provided
    if source and not _is_valid_url(source):
        source_path = Path(source)
        candidate_file = source_path / file_name
        if candidate_file.exists():
            log.info("Using local file: %s", candidate_file)
            return candidate_file
        else:
            log.error("Local file not found: %s", candidate_file)
            raise FileNotFoundError(f"Local file not found: {candidate_file}")

    # Use cached file if available and redownload is False
    cached_file = local_data_dir / file_name
    if cached_file.exists() and not redownload:
        log.info("Using cached file: %s", cached_file)
        return cached_file

    # Download if URL is provided
    if download_url:
        try:
            log.info("Downloading file from %s to %s", download_url, local_data_dir)
            return download_file(
                download_url, local_data_dir, redownload=redownload, filename=file_name
            )
        except Exception as e:
            log.error("Failed to download %s: %s", download_url, e)
            raise FileNotFoundError(f"Failed to download {download_url}: {e}")

    # If no options succeeded
    raise FileNotFoundError(
        f"File {file_name} could not be resolved from local source, cache, or remote URL.",
    )


def load_array_metadata(array_name: str) -> dict:
    """
    Load metadata YAML for a given mooring array.

    Parameters
    ----------
    array_name : str
        Name of the mooring array (e.g., 'samba').

    Returns
    -------
    dict
        Dictionary containing the parsed YAML metadata.
    """
    try:
        with (
            resources.files("amocatlas.metadata")
            .joinpath(f"{array_name.lower()}_array.yml")
            .open("r") as f
        ):
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"No metadata file found for array: {array_name}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error loading metadata for array {array_name}: {e}") from e


def safe_update_attrs(
    ds: xr.Dataset,
    new_attrs: Dict[str, str],
    overwrite: bool = False,
    verbose: bool = True,
) -> xr.Dataset:
    """Safely update attributes of an xarray Dataset without overwriting existing keys,
    unless explicitly allowed.

    Parameters
    ----------
    ds : xr.Dataset
        The xarray Dataset whose attributes will be updated.
    new_attrs : dict of str
        Dictionary of new attributes to add.
    overwrite : bool, optional
        If True, allow overwriting existing attributes. Defaults to False.
    verbose : bool, optional
        If True, emit a warning when skipping existing attributes. Defaults to True.

    Returns
    -------
    xr.Dataset
        The dataset with updated attributes.

    """
    for key, value in new_attrs.items():
        if key in ds.attrs:
            if not overwrite:
                if verbose:
                    log_debug(
                        f"Attribute '{key}' already exists in dataset attrs and will not be overwritten.",
                    )
                continue  # Skip assignment
        ds.attrs[key] = value

    return ds


# Validate the structure and required fields of an array-level metadata YAML.
REQUIRED_GLOBAL_FIELDS = [
    "project",
    "weblink",
    "time_coverage_start",
    "time_coverage_end",
]

REQUIRED_VARIABLE_FIELDS = [
    "units",
    "standard_name",
]


def validate_array_yaml(array_name: str, verbose: bool = True) -> bool:
    """
    Validate the structure and required fields of an array-level metadata YAML.

    Parameters
    ----------
    array_name : str
        The array name (e.g., 'samba').
    verbose : bool
        If True, print detailed validation messages.

    Returns
    -------
    bool
        True if validation passes, False otherwise.
    """
    try:
        meta = load_array_metadata(array_name)
    except Exception as e:
        if verbose:
            print(f"Failed to load metadata for array '{array_name}': {e}")
        return False

    success = True

    # Check required global metadata fields
    global_meta = meta.get("metadata", {})
    for field in REQUIRED_GLOBAL_FIELDS:
        if field not in global_meta:
            success = False
            if verbose:
                print(f"Missing required global metadata field: {field}")

    # Check each file's variable definitions
    for file_name, file_meta in meta.get("files", {}).items():
        variables = file_meta.get("variables", {})
        for var_name, var_attrs in variables.items():
            for field in REQUIRED_VARIABLE_FIELDS:
                if field not in var_attrs:
                    success = False
                    if verbose:
                        print(
                            f"Missing '{field}' for variable '{var_name}' in file '{file_name}'"
                        )

    if success and verbose:
        print(f"Validation passed for array '{array_name}'.")

    return success


def _validate_dims(ds: xr.Dataset) -> None:
    """Validate the dimensions of an xarray Dataset.

    This function checks if the first dimension of the dataset is named 'TIME' or 'time'.
    If not, it raises a ValueError.

    Parameters
    ----------
    ds : xr.Dataset
        The xarray Dataset to validate.

    Raises
    ------
    ValueError
        If the first dimension name is not 'TIME' or 'time'.

    """
    dim_name = list(ds.dims)[0]  # Should be 'N_MEASUREMENTS' for OG1
    if dim_name not in ["TIME", "time"]:
        raise ValueError(f"Dimension name '{dim_name}' is not 'TIME' or 'time'.")


def _is_valid_url(url: str) -> bool:
    """Validate if a given string is a valid URL with supported schemes.

    Parameters
    ----------
    url : str
        The URL string to validate.

    Returns
    -------
    bool
        True if the URL is valid and uses a supported scheme ('http', 'https', 'ftp'),
        otherwise False.

    """
    try:
        result = urlparse(url)
        return all(
            [
                result.scheme in ("http", "https", "ftp"),
                result.netloc,
                result.path,  # Ensure there's a path, not necessarily its format
            ],
        )
    except Exception:
        return False


def _is_valid_file(path: str) -> bool:
    """Check if the given path is a valid file and has a '.nc' extension.

    Parameters
    ----------
    path : str
        The file path to validate.

    Returns
    -------
    bool
        True if the path is a valid file and ends with '.nc', otherwise False.

    """
    return Path(path).is_file() and path.endswith(".nc")


def download_file(
    url: str,
    dest_folder: str,
    redownload: bool = False,
    filename: str = None,
) -> str:
    """Download a file from HTTP(S) or FTP to the specified destination folder.

    Parameters
    ----------
    url : str
        The URL of the file to download.
    dest_folder : str
        Local folder to save the downloaded file.
    redownload : bool, optional
        If True, force re-download of the file even if it exists.
    filename : str, optional
        Optional filename to save the file as. If not given, uses the name from the URL.

    Returns
    -------
    str
        The full path to the downloaded file.

    Raises
    ------
    ValueError
        If the URL scheme is unsupported.

    """
    dest_folder_path = Path(dest_folder)
    dest_folder_path.mkdir(parents=True, exist_ok=True)

    local_filename = dest_folder_path / (filename or Path(url).name)
    if local_filename.exists() and not redownload:
        # File exists and redownload not requested
        return str(local_filename)

    parsed_url = urlparse(url)

    if parsed_url.scheme in ("http", "https"):
        # HTTP(S) download
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

    elif parsed_url.scheme == "ftp":
        # FTP download
        with FTP(parsed_url.netloc) as ftp:
            ftp.login()  # anonymous login
            with open(local_filename, "wb") as f:
                ftp.retrbinary(f"RETR {parsed_url.path}", f.write)

    else:
        raise ValueError(f"Unsupported URL scheme in {url}")

    return str(local_filename)


def parse_ascii_header(
    file_path: str,
    comment_char: str = "%",
) -> Tuple[List[str], int]:
    """Parse the header of an ASCII file to extract column names and the number of header lines.

    Header lines are identified by the given comment character (default: '%').
    Columns are defined in lines like:
    '<comment_char> Column 1: <column_name>'.

    Parameters
    ----------
    file_path : str
        Path to the ASCII file.
    comment_char : str, optional
        Character used to identify header lines. Defaults to '%'.

    Returns
    -------
    tuple of (list of str, int)
        A tuple containing:
        - A list of column names extracted from the header.
        - The number of header lines to skip.

    """
    column_names: List[str] = []
    header_line_count: int = 0

    with open(file_path) as file:
        for line in file:
            line = line.strip()
            header_line_count += 1
            if line.startswith(comment_char):
                if "Column" in line and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        column_name = parts[1].strip()
                        column_names.append(column_name)
            else:
                # Stop when the first non-header line is found
                break

    return column_names, header_line_count


def read_ascii_file(file_path: str, comment_char: str = "#") -> pd.DataFrame:
    """Read an ASCII file into a pandas DataFrame, skipping lines starting with a specified comment character.

    Parameters
    ----------
    file_path : str
        Path to the ASCII file.
    comment_char : str, optional
        Character denoting comment lines. Defaults to '#'.

    Returns
    -------
    pd.DataFrame
        The loaded data as a pandas DataFrame.

    """
    return pd.read_csv(file_path, sep=r"\s+", comment=comment_char, on_bad_lines="skip")
