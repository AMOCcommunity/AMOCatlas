"""Shared utility functions for AMOCatlas readers.

This module provides common functionality used across different array readers
to eliminate code duplication while preserving the unique access patterns
of each data source (HTTP directories, per-file URLs, zip archives).

Key utilities:
- Dataset loading with consistent error handling
- Metadata attachment patterns
- File list preparation
- Data directory management
"""

from pathlib import Path
from typing import Any

import xarray as xr
import yaml

from amocatlas import logger, utilities
from amocatlas.logger import log_error, log_info, log_warning

log = logger.log

# Mapping from datasource IDs to display names for user-friendly output
DATASOURCE_DISPLAY_NAMES = {
    "rapid26n": "RAPID 26°N",
    "move16n": "MOVE 16°N",
    "osnap55n": "OSNAP",
    "samba34s": "SAMBA 34.5°S",
    "arcticgateway": "Arctic Gateway",
    "fw2015": "Frajka-Williams 2015",
    "mocha26n": "MOCHA 26°N",
    "wh41n": "Willis & Hobbs 41°N",
    "dso": "Denmark Strait Overflow",
    "noac47n": "NOAC 47°N",
    "fbc": "Faroe Bank Channel",
    "calafat2025": "Calafat et al. 2025",
    "zheng2024": "Zheng et al. 2024",
    "nac": "North Atlantic Current, M. Lankhorst, 2025",
    "sf2021": "Sanchez-Franks et al. 2021",
    "lebras35n": "Le Bras et al. 2023 at 35°N",
    "axmoc22s": "AXMOC 22.5°S",
    "axmoc34s": "AXMOC 34.5°S",
}


class ReaderUtils:
    """Shared utilities for AMOCatlas data readers."""

    @staticmethod
    def safe_load_dataset(file_path: Path, **kwargs) -> xr.Dataset:  # noqa: ANN003
        """Load an xarray Dataset with consistent error handling.

        Parameters
        ----------
        file_path : Path
            Path to the NetCDF file to load.
        **kwargs : dict
            Additional keyword arguments passed to xr.open_dataset.

        Returns
        -------
        xr.Dataset
            The loaded xarray Dataset.

        Raises
        ------
        FileNotFoundError
            If the file cannot be opened or read.

        """
        try:
            log_info("Opening dataset: %s", file_path)
            # Suppress SerializationWarning for problematic time coordinates
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="Unable to decode time axis into full numpy.datetime64",
                    category=UserWarning,
                )
                ds = xr.open_dataset(file_path, **kwargs)

            # Mask values outside valid_min/valid_max ranges
            from .utilities import mask_invalid_values

            ds = mask_invalid_values(ds)
        except (OSError, ValueError, KeyError) as e:
            log_error("Failed to open NetCDF file: %s: %s", file_path, e)
            raise FileNotFoundError(
                f"Failed to open NetCDF file: {file_path}: {e}"
            ) from e
        else:
            return ds

    @staticmethod
    def attach_standard_metadata(
        ds: xr.Dataset,
        file_name: str,
        file_path: Path,
        global_metadata: dict[str, Any],
        file_metadata: dict[str, Any],
        datasource_id: str = None,
        track_added_attrs: bool = False,
    ) -> xr.Dataset | tuple[xr.Dataset, dict[str, list[str]]]:
        """Attach standard metadata to a dataset with datasource identification.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to add metadata to.
        file_name : str
            Original filename.
        file_path : Path
            Full path to the loaded file.
        global_metadata : dict
            Global metadata for this array type.
        file_metadata : dict
            File-specific metadata.
        datasource_id : str, optional
            Unique identifier for the data source (e.g., 'rapid26n', 'samba34s').
            Used for automatic standardization function selection.
        track_added_attrs : bool, optional
            If True, return a tuple of (dataset, metadata_changes_dict).
            If False, return only the dataset. Default is False.

        Returns
        -------
        xr.Dataset or tuple[xr.Dataset, Dict[str, List[str]]]
            If track_added_attrs=False: Dataset with attached metadata.
            If track_added_attrs=True: Tuple of (dataset, dict with 'added' and 'modified' keys).

        """
        log_info("Attaching metadata to dataset from file: %s", file_name)

        # Keep track of original attributes if requested
        if track_added_attrs:
            original_attrs = dict(ds.attrs)  # Keep values to detect modifications
            original_keys = set(ds.attrs.keys())

        # Build metadata dictionary - file metadata takes precedence over YAML defaults
        # Start with YAML defaults
        metadata = {
            **global_metadata,
            **file_metadata,
        }

        # Override with original file metadata (file takes precedence)
        metadata.update(ds.attrs)

        # Add AMOCatlas-specific metadata (these are always added)
        metadata.update(
            {
                "source_file": file_name,
                "source_path": str(file_path),
            }
        )

        # Add datasource identification if provided
        if datasource_id:
            metadata["processing_datasource"] = datasource_id

        # Replace dataset attributes entirely
        ds.attrs.clear()
        ds.attrs.update(metadata)

        if track_added_attrs:
            # Find which attributes were added and modified
            new_attrs = set(ds.attrs.keys())
            added_attrs = list(new_attrs - original_keys)

            # Find modified attributes (existing keys with different values)
            modified_attrs = []
            for key in original_keys:
                if key in ds.attrs and ds.attrs[key] != original_attrs[key]:
                    modified_attrs.append(key)

            return ds, {"added": added_attrs, "modified": modified_attrs}
        return ds

    @staticmethod
    def prepare_file_list(
        file_list: str | list[str] | None,
        default_files: list[str],
        transport_files: list[str],
        transport_only: bool,
    ) -> list[str]:
        """Prepare the list of files to process.

        Parameters
        ----------
        file_list : str, list of str, or None
            User-provided file list.
        default_files : list of str
            Default files for this array.
        transport_files : list of str
            Transport-only files for this array.
        transport_only : bool
            Whether to restrict to transport files only.

        Returns
        -------
        list of str
            List of files to process.

        """
        if file_list is None:
            file_list = default_files
        if transport_only:
            file_list = transport_files
        if isinstance(file_list, str):
            file_list = [file_list]
        return file_list

    @staticmethod
    def setup_data_directory(data_dir: str | Path | None) -> Path:
        """Set up the local data directory.

        Parameters
        ----------
        data_dir : str, Path, or None
            User-provided data directory, or None for default.

        Returns
        -------
        Path
            Path to the local data directory.

        """
        local_data_dir = (
            Path(data_dir) if data_dir else utilities.get_default_data_dir()
        )
        local_data_dir.mkdir(parents=True, exist_ok=True)
        return local_data_dir

    @staticmethod
    def filter_netcdf_files(file_list: list[str]) -> list[str]:
        """Filter file list to only include NetCDF files.

        Parameters
        ----------
        file_list : list of str
            List of filenames to filter.

        Returns
        -------
        list of str
            Filtered list containing only .nc files.

        """
        netcdf_files = []
        for file in file_list:
            if file.lower().endswith(".nc"):
                netcdf_files.append(file)
            else:
                log_warning("Skipping non-NetCDF file: %s", file)
        return netcdf_files

    @staticmethod
    def print_loading_info(
        file_list: list[str],
        datasource_id: str,
        file_metadata: dict[str, dict[str, Any]],
    ) -> None:
        """Print informative output about files being loaded.

        Parameters
        ----------
        file_list : list of str
            List of files being loaded.
        datasource_id : str
            Datasource identifier (e.g., 'rapid26n', 'samba34s').
        file_metadata : dict
            Dictionary mapping filenames to their metadata dictionaries.

        """
        display_name = DATASOURCE_DISPLAY_NAMES.get(
            datasource_id, datasource_id.upper()
        )
        print(f"Loading {len(file_list)} {display_name} dataset(s):")
        for i, file in enumerate(file_list):
            description = file_metadata.get(file, {}).get(
                "data_product", "No description available"
            )
            print(f"  {i}. {file}: {description}")
        print()

    @staticmethod
    def validate_datasets_loaded(
        datasets: list[xr.Dataset], file_list: list[str]
    ) -> None:
        """Validate that datasets were successfully loaded.

        Parameters
        ----------
        datasets : list of xr.Dataset
            List of loaded datasets.
        file_list : list of str
            Original file list.

        Raises
        ------
        FileNotFoundError
            If no valid datasets were loaded.

        """
        if not datasets:
            log_error("No valid NetCDF files found in %s", file_list)
            raise FileNotFoundError(f"No valid NetCDF files found in {file_list}")

        log_info("Successfully loaded %d dataset(s)", len(datasets))

    @staticmethod
    def load_array_metadata_with_fallback(
        datasource_id: str, fallback_metadata: dict
    ) -> tuple[dict, dict]:
        """Load YAML metadata with fallback to hardcoded metadata.

        Parameters
        ----------
        datasource_id : str
            Datasource identifier (e.g., 'rapid26n', 'move16n').
        fallback_metadata : dict
            Hardcoded metadata to use if YAML loading fails.

        Returns
        -------
        tuple[dict, dict]
            (global_metadata, yaml_file_metadata)
            global_metadata: Combined metadata for dataset attributes
            yaml_file_metadata: File-specific metadata from YAML

        """
        try:
            yaml_metadata = utilities.load_array_metadata(datasource_id)
            if yaml_metadata:
                global_metadata = yaml_metadata.get("metadata", fallback_metadata)
                yaml_file_metadata = yaml_metadata.get("files", {})
                # Add the files structure to global metadata so it's attached to dataset
                global_metadata = {**global_metadata, "files": yaml_file_metadata}
            else:
                global_metadata = fallback_metadata
                yaml_file_metadata = {}
        except (FileNotFoundError, OSError, yaml.YAMLError, KeyError, TypeError) as e:
            log.warning(f"Could not load YAML metadata for {datasource_id}: {e}")
            global_metadata = fallback_metadata
            yaml_file_metadata = {}

        return global_metadata, yaml_file_metadata

    @staticmethod
    def attach_metadata_with_tracking(
        dataset: xr.Dataset,
        file: str,
        file_path: Path,
        global_metadata: dict,
        yaml_file_metadata: dict,
        fallback_file_metadata: dict,
        datasource_id: str,
        track_added_attrs: bool = False,
    ) -> xr.Dataset | tuple[xr.Dataset, dict]:
        """Attach metadata to dataset with optional attribute tracking.

        Parameters
        ----------
        dataset : xr.Dataset
            Dataset to attach metadata to.
        file : str
            Filename being processed.
        file_path : Path
            Full path to the file.
        global_metadata : dict
            Global metadata dictionary.
        yaml_file_metadata : dict
            File-specific metadata from YAML.
        fallback_file_metadata : dict
            Hardcoded file-specific metadata fallback.
        datasource_id : str
            Datasource identifier.
        track_added_attrs : bool, optional
            Whether to track which attributes were added.

        Returns
        -------
        xr.Dataset or tuple[xr.Dataset, dict]
            If track_added_attrs=False: Dataset with metadata attached.
            If track_added_attrs=True: (Dataset, attribute_changes_dict).

        """
        # Get file-specific metadata from YAML or fallback to hardcoded
        if file in yaml_file_metadata:
            file_metadata = yaml_file_metadata[file]
        else:
            file_metadata = fallback_file_metadata.get(file, {})

        if track_added_attrs:
            dataset, attr_changes = ReaderUtils.attach_standard_metadata(
                dataset,
                file,
                file_path,
                global_metadata,
                file_metadata,
                datasource_id=datasource_id,
                track_added_attrs=True,
            )
            return dataset, attr_changes
        dataset = ReaderUtils.attach_standard_metadata(
            dataset,
            file,
            file_path,
            global_metadata,
            file_metadata,
            datasource_id=datasource_id,
        )
        return dataset
