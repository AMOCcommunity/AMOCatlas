"""AMOCatlas Dataset Report Generator.

This module provides automated reporting capabilities for AMOCatlas datasets,
generating human-readable documentation with dataset statistics,
variable mappings, and quality assessments.

Features:
- Dataset analysis and statistical summaries
- Variable mapping tables (original → standardized names)
- Temporal coverage analysis
- Sphinx-compatible RST output
- Quality assessment and metadata validation

Usage:
    >>> from amocatlas import report
    >>> report_data = report.analyze_dataset("rapid26n", transport_only=True)
    >>> rst_output = report.generate_dataset_report("rapid26n")
"""

import builtins
import pandas as pd
import xarray as xr
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for automated plotting

from amocatlas import read, plotters
from amocatlas.logger import log_info, log_debug
from amocatlas.utilities import get_project_root


def _select_time_coordinate(dataset: xr.Dataset, time_coords: list) -> str:
    """Choose the canonical datetime time coordinate from candidate names.

    Prefers a coordinate named exactly ``"time"``/``"date"``, then any ``datetime64``
    coordinate, then the first candidate. Auxiliary coordinates such as ``TIME_FRACTION``
    (decimal years) also contain "time" but are not real datetimes; selecting one yields a
    nonsense record length and coverage, so they are only used as a last resort.
    """
    exact = [c for c in time_coords if c.lower() in ("time", "date")]
    if exact:
        return exact[0]
    datetime_coords = [
        c for c in time_coords if np.issubdtype(dataset[c].dtype, np.datetime64)
    ]
    return datetime_coords[0] if datetime_coords else time_coords[0]


def _reports_plots_dir() -> Path:
    """Return the report plots directory, anchored to the project root.

    The directory is resolved from the project root rather than the current
    working directory, so report generation always writes into the docs tree
    (``docs/source/_static/reports``) instead of creating a stray
    ``docs/source/_static/reports`` under wherever the caller happened to run.
    The directory is created if it does not exist.
    """
    plots_dir = get_project_root() / "docs" / "source" / "_static" / "reports"
    plots_dir.mkdir(parents=True, exist_ok=True)
    return plots_dir


class ReportUtils:
    """Shared utilities for AMOCatlas report generation."""

    @staticmethod
    def extract_contributors_and_institutions(
        datasets: List[xr.Dataset], array_name: str
    ) -> Dict[str, List[str]]:
        """Extract contributor names and institutions from dataset metadata.

        Parameters
        ----------
        datasets : List[xr.Dataset]
            List of loaded datasets with metadata
        array_name : str
            Name of the array (for tracking sources)

        Returns
        -------
        Dict[str, List[str]]
            Dictionary with 'contributors' and 'institutions' keys containing lists of names

        """
        contributors = set()
        institutions = set()

        for ds in datasets:
            # Extract contributor names
            if "contributor_name" in ds.attrs:
                contributor_name = ds.attrs["contributor_name"]
                if contributor_name and contributor_name.strip():
                    # Split by comma and clean up
                    names = [name.strip() for name in contributor_name.split(",")]
                    for name in names:
                        if name and name != "None" and name != "":
                            contributors.add(name)

            # Extract contributing institutions
            for attr_key in [
                "contributing_institutions",
                "contributing_institution",
                "institution",
            ]:
                if attr_key in ds.attrs:
                    institution = ds.attrs[attr_key]
                    if institution and institution.strip():
                        # Split by comma and clean up
                        inst_list = [inst.strip() for inst in institution.split(",")]
                        for inst in inst_list:
                            if inst and inst != "None" and inst != "":
                                institutions.add(inst)

        return {
            "contributors": sorted(list(contributors)),
            "institutions": sorted(list(institutions)),
            "array_source": array_name,
        }

    @staticmethod
    def update_contributors_database(
        contributors_data: Dict[str, List[str]], db_file: Path = None
    ) -> Path:
        """Update the global contributors database file.

        Parameters
        ----------
        contributors_data : Dict[str, List[str]]
            Dictionary with contributor and institution data from extract_contributors_and_institutions
        db_file : Path, optional
            Path to the database file. Defaults to 'contributors_database.yml' in project root.

        Returns
        -------
        Path
            Path to the updated database file

        """
        import yaml
        from pathlib import Path

        if db_file is None:
            # Store in project root as YAML
            db_file = Path.cwd() / "contributors_database.yml"

        # Load existing database or create new one
        database = {}
        if db_file.exists():
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    database = yaml.safe_load(f) or {}
            except (yaml.YAMLError, UnicodeDecodeError):
                log_info(f"Creating new contributors database at {db_file}")
                database = {}

        # Initialize database structure if needed
        if "arrays" not in database:
            database["arrays"] = {}
        if "all_contributors" not in database:
            database["all_contributors"] = []
        if "all_institutions" not in database:
            database["all_institutions"] = []

        # Convert lists back to sets for processing
        all_contributors = set(database.get("all_contributors", []))
        all_institutions = set(database.get("all_institutions", []))

        # Update with new data
        array_name = contributors_data["array_source"]
        database["arrays"][array_name] = {
            "contributors": contributors_data["contributors"],
            "institutions": contributors_data["institutions"],
            "last_updated": datetime.now().strftime("%Y-%m"),
        }

        # Update global sets
        all_contributors.update(contributors_data["contributors"])
        all_institutions.update(contributors_data["institutions"])

        # Convert back to sorted lists
        database["all_contributors"] = sorted(list(all_contributors))
        database["all_institutions"] = sorted(list(all_institutions))

        # Write updated database with human-friendly YAML format
        with open(db_file, "w", encoding="utf-8") as f:
            # Write header comment
            f.write("# AMOCatlas Contributors Database\n")
            f.write("# Generated automatically during report generation\n")
            f.write(
                "# This file tracks all contributors and institutions across datasets\n"
            )
            f.write(
                "# Use this for ORCID lookup and institutional identifier research\n\n"
            )

            # Write the data
            yaml.dump(
                database,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=100,
            )

        log_info(
            f"Updated contributors database: {len(database['all_contributors'])} contributors, "
            f"{len(database['all_institutions'])} institutions"
        )

        return db_file

    @staticmethod
    def handle_yyyymm_time_format(
        time_data: Union[xr.DataArray, pd.Series, np.ndarray],
    ) -> pd.Series:
        """Handle YYYYMM time format (e.g., 200201 = February 2002)."""
        try:
            time_values = time_data.values
            # Convert YYYYMM to datetime: 200201 -> 2002-01-01
            datetime_strings = []
            for val in time_values:
                year = val // 100
                month = val % 100
                if month == 0:
                    month = 1  # Handle edge case
                datetime_strings.append(f"{year}-{month:02d}-01")
            return pd.to_datetime(datetime_strings)
        except (ValueError, TypeError, OverflowError, pd.errors.OutOfBoundsDatetime):
            # Fallback to regular conversion
            return pd.to_datetime(time_data.values)

    @staticmethod
    def estimate_frequency(
        median_diff: Union[pd.Timedelta, np.timedelta64, float, int],
    ) -> str:
        """Estimate sampling frequency from median time difference."""
        try:
            # Handle pandas Timedelta
            if hasattr(median_diff, "total_seconds"):
                hours = median_diff.total_seconds() / 3600
            else:
                # Handle numeric difference - need to determine the units
                diff_value = float(median_diff)

                # Heuristic to determine time units based on typical values:
                # - If diff > 1000, likely seconds (typical: 3600s=1h, 43200s=12h)
                # - If 1 < diff < 100, likely days (typical: 1day, 30days)
                # - If diff < 1, likely fractional days
                if diff_value > 1000:
                    # Assume seconds
                    hours = diff_value / 3600
                elif diff_value > 1:
                    # Assume days
                    hours = diff_value * 24
                else:
                    # Assume fractional days
                    hours = diff_value * 24
        except (ValueError, TypeError, AttributeError, OverflowError):
            return "unknown"

        if hours < 1:
            try:
                if hasattr(median_diff, "total_seconds"):
                    minutes = int(median_diff.total_seconds() // 60)
                    # Round frequencies close to 60 minutes to hourly
                    if minutes >= 55:
                        return "hourly"
                    else:
                        return f"{minutes}min"
                else:
                    return "<1H"
            except (ValueError, TypeError, ZeroDivisionError):
                # Handle calculation errors when determining frequency
                return "<1H"
        elif 11 <= hours <= 13:
            return "12H"
        elif hours < 12:
            return f"{hours:.1f}H"
        elif 20 <= hours <= 28:
            return "daily"
        elif 28 <= hours <= 35:
            return "monthly"
        elif 720 <= hours <= 760:  # ~30-31 days
            return "monthly"
        elif 2000 <= hours <= 2300:  # ~3 months (quarterly)
            return "3-monthly"
        elif 4000 <= hours <= 4500:  # ~6 months
            return "6-monthly"
        elif 8000 <= hours <= 9000:  # ~12 months (annual)
            return "annual"
        else:
            return f"{hours:.1f}H"

    @staticmethod
    def compute_dataset_statistics(dataset: xr.Dataset) -> Dict[str, Any]:
        """Compute dataset statistics."""
        stats = {
            "total_variables": len(dataset.data_vars),
            "total_coordinates": len(dataset.coords),
            "total_attributes": len(dataset.attrs),
            "file_size_mb": dataset.nbytes / (1024 * 1024),
            "variables": {},
            "coordinates": {},
        }

        # Compute statistics for each data variable
        for var_name, var in dataset.data_vars.items():
            var_stats = {
                "dtype": str(var.dtype),
                "shape": var.shape,
                "dimensions": list(var.dims),
                "has_time": "time" in var.dims or "TIME" in var.dims,
                "units": var.attrs.get("units", "unknown"),
                "long_name": var.attrs.get("long_name", var_name),
                "missing_data_pct": 0.0,
            }

            # Compute min/max/mean for numeric variables
            if np.issubdtype(var.dtype, np.number):
                # Handle potential NaN values
                valid_data = var.where(np.isfinite(var), drop=True)
                if valid_data.size > 0:
                    var_stats.update(
                        {
                            "min": float(valid_data.min().values),
                            "max": float(valid_data.max().values),
                            "mean": float(valid_data.mean().values),
                            "std": float(valid_data.std().values),
                        }
                    )
                    # Calculate missing data percentage
                    total_size = var.size
                    valid_size = valid_data.size
                    var_stats["missing_data_pct"] = (
                        (total_size - valid_size) / total_size
                    ) * 100

            stats["variables"][var_name] = var_stats

        # Compute statistics for each coordinate
        for coord_name, coord in dataset.coords.items():
            coord_stats = {
                "dtype": str(coord.dtype),
                "shape": coord.shape,
                "dimensions": list(coord.dims),
                "units": coord.attrs.get("units", "unknown"),
                "long_name": coord.attrs.get("long_name", coord_name),
                "missing_data_pct": 0.0,
            }

            # Compute min/max for numeric coordinates
            if np.issubdtype(coord.dtype, np.number):
                # Handle potential NaN values
                valid_data = coord.where(np.isfinite(coord), drop=True)
                if valid_data.size > 0:
                    coord_stats.update(
                        {
                            "min": float(valid_data.min().values),
                            "max": float(valid_data.max().values),
                            "mean": float(valid_data.mean().values),
                        }
                    )
                else:
                    coord_stats.update({"min": None, "max": None, "mean": None})
            elif coord.dtype.kind == "M":  # Datetime
                coord_stats.update(
                    {
                        "min": str(coord.min().values)[:10],
                        "max": str(coord.max().values)[:10],
                    }
                )
            else:
                # For non-numeric coordinates, just store first and last values
                coord_stats.update(
                    {
                        "min": str(coord.values[0]) if coord.size > 0 else None,
                        "max": str(coord.values[-1]) if coord.size > 0 else None,
                    }
                )

            stats["coordinates"][coord_name] = coord_stats

        return stats

    @staticmethod
    def safe_time_diff_days(
        time_max: Union[datetime, pd.Timestamp, np.datetime64, float, int],
        time_min: Union[datetime, pd.Timestamp, np.datetime64, float, int],
    ) -> float:
        """Safely calculate time difference in days, handling different data types."""
        try:
            # Try standard datetime difference first
            diff = time_max - time_min
            if hasattr(diff, "days"):
                return diff.days
            else:
                # Handle numeric time values
                try:
                    numeric_diff = float(diff)
                    max_val = max(abs(float(time_max)), abs(float(time_min)))

                    # Check for obviously invalid/sentinel values (very large negative numbers)
                    if (
                        max_val > 1e10
                    ):  # Very large values likely indicate data corruption
                        # Return 0 to avoid wildly incorrect time spans
                        return 0

                    # Check if these look like YYYYMM format (e.g., 200201, 202412)
                    if 190000 <= max_val <= 300000 and abs(numeric_diff) < 10000:
                        # Convert YYYYMM to actual dates and calculate difference
                        try:
                            # Convert YYYYMM to datetime
                            min_year = int(time_min) // 100
                            min_month = int(time_min) % 100
                            max_year = int(time_max) // 100
                            max_month = int(time_max) % 100

                            min_date = datetime(min_year, min_month, 1)
                            max_date = datetime(max_year, max_month, 1)

                            return (max_date - min_date).days
                        except (ValueError, TypeError):
                            # Fallback to rough approximation if conversion fails
                            return abs(numeric_diff) * 30.44

                    # Check if the values look like unix timestamps (> 1e9)
                    elif max_val > 1e9:
                        # Assume difference is in seconds, convert to days
                        return abs(numeric_diff) / 86400.0  # seconds to days

                    # Check if values are small and could be decimal years since some reference
                    elif max_val < 100:
                        # Likely decimal years (e.g., 0.95, 1.66)
                        # These are probably years since 2000 or similar
                        return abs(numeric_diff) * 365.25

                    else:
                        # Other numeric formats - be conservative and assume days
                        return abs(numeric_diff)

                except (ValueError, TypeError):
                    return 0
        except (AttributeError, ValueError, TypeError, OverflowError):
            # Fallback for any other cases
            return 0

    @staticmethod
    def safe_format_date(
        date_obj: Union[datetime, pd.Timestamp, np.datetime64, float, int, str],
    ) -> str:
        """Safely format date, handling different data types."""
        try:
            if hasattr(date_obj, "strftime"):
                return date_obj.strftime("%Y-%m-%d")
            else:
                # Check if this looks like seconds since 1970 (unix timestamp)
                try:
                    numeric_val = float(date_obj)
                    if numeric_val > 1e9:  # Likely seconds since 1970
                        return pd.to_datetime(numeric_val, unit="s").strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        # Assume it's a year
                        return f"{numeric_val:.1f}"
                except (ValueError, TypeError):
                    return str(date_obj)
        except (
            AttributeError,
            ValueError,
            TypeError,
            OverflowError,
            pd.errors.OutOfBoundsDatetime,
        ):
            return str(date_obj)

    @staticmethod
    def analyze_temporal_coverage(dataset: xr.Dataset) -> Dict[str, Any]:
        """Analyze temporal coverage of the dataset."""
        # Find time coordinate
        time_coords = []
        for coord_name in dataset.coords:
            if coord_name.lower() in ["time", "date"] or "time" in coord_name.lower():
                time_coords.append(coord_name)

        if not time_coords:
            return {"has_time": False}

        time_coord = _select_time_coordinate(dataset, time_coords)
        time_data = dataset[time_coord]

        # Convert to pandas datetime if needed
        if hasattr(time_data, "to_pandas"):
            time_series = time_data.to_pandas()
        else:
            time_values = time_data.values
            # Handle different time formats
            if hasattr(time_values, "__iter__") and len(time_values) > 0:
                # Check the dtype first
                if str(time_data.dtype).startswith("datetime64"):
                    # Already datetime64, just convert to pandas
                    time_series = pd.to_datetime(time_values)
                else:
                    # Check for YYYYMM format first
                    units = time_data.attrs.get("units", "").upper()
                    if units == "YYYYMM" or (
                        len(time_values) > 0
                        and isinstance(time_values[0], (int, np.integer))
                        and 190000 <= time_values[0] <= 300000
                    ):
                        # Handle YYYYMM format
                        time_series = ReportUtils.handle_yyyymm_time_format(time_data)
                    else:
                        # Numeric values - check if they look like seconds since 1970
                        try:
                            sample_val = float(time_values[0])
                            if sample_val > 1e9:  # Likely seconds since 1970
                                time_series = pd.to_datetime(time_values, unit="s")
                            else:
                                time_series = pd.to_datetime(time_values)
                        except (ValueError, TypeError):
                            time_series = pd.to_datetime(time_values)
            else:
                time_series = pd.to_datetime(time_values)

        # Remove invalid times and extreme outliers
        valid_times = time_series.dropna()

        # Filter out extremely unrealistic dates (e.g., from sentinel values)
        # Keep only dates between 1900 and 2100 (reasonable range for oceanographic data)
        try:
            min_year = pd.Timestamp("1900-01-01")
            max_year = pd.Timestamp("2100-01-01")
            valid_times = valid_times[
                (valid_times >= min_year) & (valid_times <= max_year)
            ]
        except (TypeError, ValueError):
            # If date filtering fails, just keep the dropna() result
            pass

        if len(valid_times) == 0:
            return {"has_time": True, "valid_times": False}

        # Calculate temporal statistics
        start_date = valid_times.min()
        end_date = valid_times.max()

        time_info = {
            "has_time": True,
            "valid_times": True,
            "coordinate_name": time_coord,
            "start_date": start_date,
            "end_date": end_date,
            "total_records": len(valid_times),
            "time_span_days": ReportUtils.safe_time_diff_days(end_date, start_date),
            "time_span_years": ReportUtils.safe_time_diff_days(end_date, start_date)
            / 365.25,
        }

        # Estimate sampling frequency
        if len(valid_times) > 1:
            time_diffs = valid_times.diff().dropna()
            median_diff = time_diffs.median()
            time_info["median_sampling_interval"] = median_diff
            time_info["estimated_frequency"] = ReportUtils.estimate_frequency(
                median_diff
            )

            # Add warnings for problematic values
            warnings = []

            # Check for extremely long record length (>50 years)
            if time_info["time_span_years"] > 50:
                warnings.append(
                    f"WARNING: Record length of {time_info['time_span_years']:.1f} years seems unusually long"
                )

            # Check for extremely high sampling frequency values (>5000 hours = ~7 months)
            # Allow quarterly data (~2200H) and other reasonable oceanographic intervals
            freq_str = time_info["estimated_frequency"]
            if freq_str.endswith("H") and not freq_str.endswith("min"):
                try:
                    freq_hours = float(freq_str.replace("H", ""))
                    if freq_hours > 5000:
                        warnings.append(
                            f"WARNING: Sampling frequency of {freq_hours}H seems unusually high - possible time parsing issue"
                        )
                except ValueError:
                    # Skip frequency check if conversion to float fails
                    pass

            if warnings:
                time_info["warnings"] = warnings
                for warning in warnings:
                    print(f"  {warning}")

        return time_info

    @staticmethod
    def create_coordinate_info_table(dataset: xr.Dataset) -> pd.DataFrame:
        """Create coordinate information table from dataset coordinates."""
        coord_data = []

        for coord_name in dataset.coords:
            coord_var = dataset[coord_name]

            # Basic coordinate info
            coord_info = {
                "Coordinate": coord_name,
                "Standardized Name": coord_name,  # No mapping for raw data
                "Description": coord_var.attrs.get(
                    "long_name",
                    coord_var.attrs.get("description", "No description available"),
                ),
                "Units": coord_var.attrs.get("units", str(coord_var.dtype)),
                "Size": str(coord_var.shape),
                "Min Value": "",  # Will fill below
                "Max Value": "",  # Will fill below
            }

            # Try to get min/max values
            try:
                # Special handling for TIME coordinates
                if coord_name == "TIME":
                    # Handle different TIME coordinate formats
                    if coord_var.dtype.kind == "M":  # datetime64 type
                        # Convert datetime64 directly to readable dates
                        min_date = pd.to_datetime(coord_var.min().values).strftime(
                            "%Y-%m-%d"
                        )
                        max_date = pd.to_datetime(coord_var.max().values).strftime(
                            "%Y-%m-%d"
                        )
                        coord_info["Min Value"] = min_date
                        coord_info["Max Value"] = max_date
                    elif coord_var.attrs.get("units", "").startswith(
                        "seconds since 1970"
                    ):
                        # Handle seconds since 1970 (standardized format)
                        min_timestamp = float(coord_var.min())
                        max_timestamp = float(coord_var.max())

                        min_date = pd.to_datetime(min_timestamp, unit="s").strftime(
                            "%Y-%m-%d"
                        )
                        max_date = pd.to_datetime(max_timestamp, unit="s").strftime(
                            "%Y-%m-%d"
                        )

                        coord_info["Min Value"] = min_date
                        coord_info["Max Value"] = max_date
                    else:
                        # Fallback to numeric handling
                        coord_info["Min Value"] = f"{float(coord_var.min()):.2f}"
                        coord_info["Max Value"] = f"{float(coord_var.max()):.2f}"
                elif coord_var.dtype.kind in ["f", "i"]:  # Numeric data
                    coord_info["Min Value"] = f"{float(coord_var.min()):.2f}"
                    coord_info["Max Value"] = f"{float(coord_var.max()):.2f}"
                elif coord_var.dtype.kind == "M":  # Datetime
                    coord_info["Min Value"] = str(coord_var.min().values)[
                        :10
                    ]  # Just date part
                    coord_info["Max Value"] = str(coord_var.max().values)[
                        :10
                    ]  # Just date part
                else:
                    coord_info["Min Value"] = str(coord_var.values[0])
                    coord_info["Max Value"] = str(coord_var.values[-1])
            except (
                ValueError,
                TypeError,
                IndexError,
                AttributeError,
                pd.errors.OutOfBoundsDatetime,
            ):
                coord_info["Min Value"] = "N/A"
                coord_info["Max Value"] = "N/A"

            coord_data.append(coord_info)

        return pd.DataFrame(coord_data)

    @staticmethod
    def create_varcoord_table(
        dataset: xr.Dataset,
        statistics: Dict[str, Any],
        _metadata: Dict[str, Any],
        table_type: str = "variables",
    ) -> pd.DataFrame:
        """Create unified variable or coordinate mapping table.

        Parameters
        ----------
        dataset : xr.Dataset
            Dataset to process
        statistics : Dict[str, Any]
            Dataset statistics
        metadata : Dict[str, Any]
            Dataset metadata
        table_type : str
            Either "variables" or "coordinates"

        Returns
        -------
        pd.DataFrame
            Table with variable/coordinate information

        """
        # For standardized reports, use ONLY dataset attributes - no YAML metadata
        # Get the applied variable mapping from the standardized dataset
        _variable_mapping = dataset.attrs.get("applied_variable_mapping", {})

        mapping_data = []

        # Get applied variable mapping from dataset attributes (shows original -> standardized)
        applied_mapping = dataset.attrs.get("applied_variable_mapping", {})

        # Create reverse mapping: standardized -> original for display purposes
        # Prioritize actual renames over identity mappings
        reverse_mapping = {}
        for orig_var, std_var in applied_mapping.items():
            if orig_var != std_var:
                # This is an actual rename - use it
                reverse_mapping[std_var] = orig_var
            elif std_var not in reverse_mapping:
                # This is an identity mapping - only use if no actual rename exists
                reverse_mapping[std_var] = orig_var

        # Get items to process based on table type
        if table_type == "variables":
            items_to_process = sorted(dataset.data_vars)
            stats_key = "variables"
        else:  # coordinates
            items_to_process = sorted(dataset.coords)
            stats_key = "coordinates"

        # Iterate through items in order
        for item_name in items_to_process:
            item_data = dataset[item_name]
            item_stats = statistics.get(stats_key, {}).get(item_name, {})

            # Create display name using new format: *orig* → **standardized** or just **standardized**
            if item_name in reverse_mapping:
                # This item is in the mapping - check if it was actually renamed
                orig_name = reverse_mapping[item_name]
                if orig_name != item_name:
                    # Only show mapping if names are actually different (case-sensitive)
                    display_name = f"*{orig_name}* → **{item_name}**"
                else:
                    # Names are identical - no rename occurred
                    display_name = f"**{item_name}**"
            else:
                # This item was not in the mapping at all
                display_name = f"**{item_name}**"

            # Get description and long_name from standardized dataset attributes only
            description = item_data.attrs.get("description", "")
            long_name = item_data.attrs.get("long_name", "")

            # Create display description: prioritize description, then add long_name in bold
            if description:
                if long_name and long_name != description:
                    display_description = f"**{long_name}**: {description}"
                else:
                    display_description = description
            elif long_name and long_name != item_name:
                display_description = long_name
            else:
                display_description = "No description available"

            # Get size from item - show shape instead of total elements
            if hasattr(item_data, "shape"):
                size = str(item_data.shape)
            elif hasattr(item_data, "size"):
                size = str(item_data.size)
            else:
                size = "unknown"

            # Handle min/max values differently for coordinates vs variables
            if table_type == "coordinates" and item_name == "TIME":
                # Special handling for TIME coordinates
                try:
                    if item_data.dtype.kind == "M":  # datetime64 type
                        min_val = pd.to_datetime(item_data.min().values).strftime(
                            "%Y-%m-%d"
                        )
                        max_val = pd.to_datetime(item_data.max().values).strftime(
                            "%Y-%m-%d"
                        )
                    elif item_data.attrs.get("units", "").startswith(
                        "seconds since 1970"
                    ):
                        # Handle seconds since 1970 (standardized format)
                        min_timestamp = float(item_data.min())
                        max_timestamp = float(item_data.max())
                        min_val = pd.to_datetime(min_timestamp, unit="s").strftime(
                            "%Y-%m-%d"
                        )
                        max_val = pd.to_datetime(max_timestamp, unit="s").strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        min_val = str(item_stats.get("min", "N/A"))
                        max_val = str(item_stats.get("max", "N/A"))
                except (ValueError, TypeError, AttributeError):
                    min_val = str(item_stats.get("min", "N/A"))
                    max_val = str(item_stats.get("max", "N/A"))
            else:
                min_val = item_stats.get("min", "N/A")
                max_val = item_stats.get("max", "N/A")

            # Create row - column names depend on table type
            if table_type == "variables":
                column_name = "Variable"
            else:
                column_name = "Coordinate"

            row = {
                column_name: display_name,
                "Description": display_description,
                "Units": item_data.attrs.get("units", "unknown"),
                "Size": size,
                "Min Value": min_val,
                "Max Value": max_val,
                "Missing %": f"{item_stats.get('missing_data_pct', 0.0):.1f}%",
            }

            # Add additional columns for variables only
            if table_type == "variables":
                row.update(
                    {
                        "Data Type": item_stats.get("dtype", "unknown"),
                        "Dimensions": str(item_stats.get("dimensions", [])),
                    }
                )

            mapping_data.append(row)

        return pd.DataFrame(mapping_data)

    @staticmethod
    def create_variable_mapping_table(
        dataset: xr.Dataset, statistics: Dict[str, Any], metadata: Dict[str, Any]
    ) -> pd.DataFrame:
        """Create variable mapping table from dataset metadata and statistics."""
        return ReportUtils.create_varcoord_table(
            dataset, statistics, metadata, table_type="variables"
        )

    @staticmethod
    def generate_plot(dataset: xr.Dataset, dataset_name: str) -> Optional[str]:
        """Generate a plot for the dataset and return the relative path."""
        try:
            plots_dir = _reports_plots_dir()

            # Generate base filename (clean dataset name for filename)
            clean_name = dataset_name.replace(" ", "_").replace(".nc", "").lower()

            # Find 1-dimensional time series variables indexed against time
            data_vars = list(dataset.data_vars.keys())
            time_coords = [coord for coord in dataset.coords if "time" in coord.lower()]

            if not time_coords:
                print(f"  No time coordinate found in {dataset_name}")
                return None

            time_coord = _select_time_coordinate(dataset, time_coords)

            # Find 1D time series and 2D variables
            timeseries_vars = []
            twod_vars = []
            for var in data_vars:
                var_data = dataset[var]
                # Check if variable is 1D and has time as its dimension
                if (
                    len(var_data.dims) == 1
                    and time_coord in var_data.dims
                    and var_data.dtype.kind in ["f", "i"]  # numeric
                    and "flag" not in var.lower()
                ):  # not a flag variable
                    timeseries_vars.append(var)
                # Check for 2D variables with single element in non-time dimension (treat as 1D)
                elif (
                    len(var_data.dims) == 2
                    and time_coord in var_data.dims
                    and var_data.dtype.kind in ["f", "i"]  # numeric
                    and "flag" not in var.lower()
                    and any(
                        var_data.shape[i] == 1
                        for i, dim in enumerate(var_data.dims)
                        if dim != time_coord
                    )
                ):  # 2D with single element in non-time dimension
                    timeseries_vars.append(var)
                # Check if variable is 2D with time and another dimension (true 2D)
                elif (
                    len(var_data.dims) == 2
                    and time_coord in var_data.dims
                    and var_data.dtype.kind in ["f", "i"]  # numeric
                    and "flag" not in var.lower()
                    and builtins.all(
                        var_data.shape[i] > 1
                        for i, dim in enumerate(var_data.dims)
                        if dim != time_coord
                    )
                ):  # true 2D variable
                    twod_vars.append(var)

            # Determine plotting strategy. An explicit per-array override
            # (metadata `report_plot_variable`) wins; otherwise fall back to a
            # keyword-priority heuristic (2D preferred, then 1D time series).
            plot_2d = False
            var_to_plot = None
            plot_type = "Time Series"

            override_var = dataset.attrs.get("report_plot_variable")
            if override_var:
                if override_var in twod_vars:
                    var_to_plot, plot_2d, plot_type = override_var, True, "2D Data"
                elif override_var in timeseries_vars:
                    var_to_plot, plot_2d, plot_type = override_var, False, "Time Series"
                else:
                    print(
                        f"  report_plot_variable {override_var!r} is not a plottable "
                        f"time series in {dataset_name}; using heuristic"
                    )

            if var_to_plot is None:
                # Priority order for 2D variables (using standardized names)
                twod_priority = [
                    "streamfunction",
                    "vcur",  # Standardized name for meridional velocity
                    "temperature",
                    "temp",  # Temperature variables
                    "moc",
                    "sal",
                    "density",
                    "profile",
                ]

                # Find best 2D variable based on priority
                for priority_term in twod_priority:
                    matching_vars = [
                        var for var in twod_vars if priority_term in var.lower()
                    ]
                    if matching_vars:
                        var_to_plot = matching_vars[0]
                        plot_type = "2D Data"
                        plot_2d = True
                        break

                if not plot_2d and twod_vars:
                    # Any other 2D variable
                    var_to_plot = twod_vars[0]
                    plot_type = "2D Data"
                    plot_2d = True

                if not plot_2d:
                    # Fall back to 1D time series
                    if not timeseries_vars:
                        print(
                            f"  No suitable variables found for plotting in {dataset_name}"
                        )
                        return None

                    # Priority order for 1D variables
                    oned_priority = [
                        "moc",
                        "mht",
                        "trans",
                        "transport",
                        "_t_",
                        "t_",
                        "stream",
                        "temp",
                        "tg_",
                    ]

                    # Find best 1D variable based on priority
                    for priority_term in oned_priority:
                        matching_vars = [
                            var
                            for var in timeseries_vars
                            if priority_term in var.lower()
                        ]
                        if matching_vars:
                            var_to_plot = matching_vars[0]
                            if "moc" in priority_term:
                                plot_type = "MOC"
                            elif "mht" in priority_term:
                                plot_type = "Heat Transport"
                            elif any(
                                x in priority_term
                                for x in ["trans", "transport", "_t_", "t_", "stream"]
                            ):
                                plot_type = "Transport"
                            elif any(x in priority_term for x in ["temp", "tg_"]):
                                plot_type = "Temperature"
                            else:
                                plot_type = "Time Series"
                            break

                    if var_to_plot is None:
                        var_to_plot = timeseries_vars[0]
                        plot_type = "Time Series"

            print(
                f"  Generating plot for {dataset_name} using variable: {var_to_plot} ({'2D' if plot_2d else '1D'})"
            )

            # Generate plot filename based on plot type
            if plot_2d:
                plot_filename = f"{clean_name}_2d_gridded.png"
            else:
                plot_filename = f"{clean_name}_timeseries.png"
            plot_path = plots_dir / plot_filename

            # Use appropriate plotter based on data dimensions
            title = f"{dataset_name.upper()} {plot_type}"

            if plot_2d:
                # Use 2D plotting function
                fig, ax = plotters.plot_amoc_2d_data(
                    dataset,
                    varname=var_to_plot,
                    title=title,
                    figsize=(8, 4),
                )
            else:
                # Use 1D time series plotting function
                fig, ax = plotters.plot_amoc_timeseries(
                    dataset,
                    varnames=[var_to_plot],
                    title=title,
                    resample_monthly=False,
                    plot_raw=True,
                    figsize=(8, 3),
                )

            # Customize plot
            if hasattr(fig, "get_axes") and fig.get_axes():
                ax = fig.get_axes()[0]
                if hasattr(ax, "legend"):
                    # Only create legend if there are labeled artists
                    handles, labels = ax.get_legend_handles_labels()
                    if handles:
                        legend = ax.legend()
                        if legend:
                            legend.set_visible(False)

            # Save plot (suppress matplotlib metadata for deterministic output)
            fig.savefig(
                plot_path,
                dpi=150,
                bbox_inches="tight",
                facecolor="white",
                metadata={"Software": None, "Creation Time": None},
            )

            # Import matplotlib.pyplot if not already imported
            try:
                import matplotlib.pyplot as plt

                plt.close(fig)
            except ImportError:
                # matplotlib not available - can't close figure
                pass

            # Return relative path for Sphinx (from reports directory)
            plot_path_return = f"../_static/reports/{plot_filename}"

        except Exception as e:
            print(f"  Warning: Failed to generate plot for {dataset_name}: {e}")
            log_debug(f"Plot generation failed for {dataset_name}: {e}")
            return None
        else:
            return plot_path_return

    @staticmethod
    def generate_array_report(
        array_name: str,
        all_files: bool = True,
        output_file: str = None,
        canonical_dates: bool = False,
    ) -> str:
        """Generate a report for any array following the read.{array}() pattern.

        Parameters
        ----------
        array_name : str
            Name of the array (e.g., 'rapid', 'osnap', 'move', 'samba')
        all_files : bool, optional
            Whether to include all files in the report, by default True
        output_file : str, optional
            If specified, write the report to this file in addition to returning it
        canonical_dates : bool, optional
            If True, use canonical dates for documentation to avoid git churn.
            Sets date_modified to first day of current month (e.g., 2026-02-01T00:00:00Z).
            By default False (uses actual timestamps)

        Returns
        -------
        str
            RST content of the report

        Notes
        -----
        This function uses track_added_attrs=True internally to track metadata changes
        during data loading. The '_amocatlas_metadata_changes' attribute is temporarily
        embedded in each dataset and then extracted/removed during report generation.

        Examples
        --------
        >>> from amocatlas.report import ReportUtils
        >>> rst_content = ReportUtils.generate_array_report('rapid')
        >>> rst_content = ReportUtils.generate_array_report('osnap', all_files=False)

        """
        from amocatlas import read

        print(f"Loading {array_name.upper()} datasets for report generation...")

        # Get the read function for this array
        read_func = getattr(read, array_name.lower())

        # Load datasets with attribute tracking (if supported)
        try:
            # Try with tracking first
            result = read_func(
                all_files=all_files,
                transport_only=not all_files,  # If all_files=False, only transport
                track_added_attrs=True,
                raw=False,  # Use standardized data
            )
        except TypeError as e:
            if "track_added_attrs" in str(e):
                # Reader doesn't support tracking, use without it
                print(
                    f"  Note: {array_name} reader doesn't support metadata tracking yet"
                )
                result = read_func(
                    all_files=all_files,
                    transport_only=not all_files,
                    track_added_attrs=False,
                    raw=False,
                )
            else:
                raise

        # Extract datasets and metadata changes (now embedded in dataset attributes)
        if isinstance(result, list):
            datasets = result
        else:
            datasets = [result]

        # Extract metadata changes from dataset attributes
        attr_changes_list = []
        for ds in datasets:
            # Pop the embedded metadata changes (removes it from dataset)
            changes = ds.attrs.pop(
                "_amocatlas_metadata_changes", {"added": [], "modified": []}
            )
            attr_changes_list.append(changes)

        print(f"Loaded {len(datasets)} {array_name.upper()} datasets")

        # Apply canonical dates for documentation if requested
        if canonical_dates:
            print("  Applying canonical dates for documentation (avoiding git churn)")
            # Use first day of current month for canonical date
            from datetime import datetime

            now = datetime.now()
            canonical_date = f"{now.year}-{now.month:02d}-01T00:00:00Z"

            for ds in datasets:
                # Set canonical date_modified to avoid changing every time
                ds.attrs["date_modified"] = canonical_date

        # Extract and store contributors and institutions
        try:
            contributors_data = ReportUtils.extract_contributors_and_institutions(
                datasets, array_name
            )
            ReportUtils.update_contributors_database(contributors_data)
            print(
                f"  Updated contributors database: {len(contributors_data['contributors'])} contributors, "
                f"{len(contributors_data['institutions'])} institutions"
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            log_info(f"Warning: Failed to extract contributors for {array_name}: {e}")

        if len(datasets) == 1:
            # Single dataset - use standard report generation
            dataset = datasets[0]
            attr_changes = attr_changes_list[0]

            report_data = StandardizedDatasetReport(
                f"{array_name.upper()}", dataset, attr_changes
            )
            rst_content = _generate_rst_report(report_data)

        else:
            # Multiple datasets - create combined report
            lines = []
            lines.extend(
                [
                    f"{array_name.upper()} Datasets",
                    "=" * (len(array_name) + 9),
                    "",
                    f"This report covers all available {array_name.upper()} datasets.",
                    "",
                ]
            )

            for i, (dataset, attr_changes) in enumerate(
                zip(datasets, attr_changes_list, strict=False)
            ):
                source_file = dataset.attrs.get("source_file", f"dataset_{i}")
                print(f"Processing {source_file}...")

                try:
                    # Create report for this individual dataset (use just source_file as name)
                    report_data = StandardizedDatasetReport(
                        source_file.replace(".nc", ""), dataset, attr_changes
                    )

                    # Generate individual report and extract content
                    individual_rst = _generate_rst_report(
                        report_data, skip_source_header=True
                    )
                    rst_lines = individual_rst.split("\n")

                    # Separate datasets with a horizontal rule — but not before the first,
                    # since a document may not begin with a transition.
                    if i > 0:
                        lines.extend(["----", ""])
                    lines.extend(
                        [
                            source_file,
                            "-" * len(source_file),
                            "",
                        ]
                    )

                    # Find where the actual content starts (skip the main title and header)
                    content_start = 0
                    skip_title = True
                    for j, line in enumerate(rst_lines):
                        if skip_title and line.startswith("====="):
                            # Found end of title, skip next few lines
                            content_start = j + 3
                            skip_title = False
                            # Continue looking for "Dataset Overview" instead of breaking
                        elif line.startswith("Dataset Overview") or line.startswith(
                            "Coordinate Information"
                        ):
                            content_start = j
                            break

                    # Add the content (everything after the main title)
                    if content_start > 0 and content_start < len(rst_lines):
                        for line in rst_lines[content_start:]:
                            lines.append(line)
                    else:
                        # Fallback to basic info if parsing fails
                        lines.extend(
                            [
                                "Dataset Overview",
                                "^^^^^^^^^^^^^^^^",
                                "",
                                f"- **Source File**: {source_file}",
                                f"- **Variables**: {list(dataset.data_vars.keys())}",
                                f"- **Coordinates**: {list(dataset.coords.keys())}",
                                "",
                                "Note: Full report generation failed - showing basic information.",
                                "",
                            ]
                        )

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    AttributeError,
                    IndexError,
                ) as e:
                    print(f"Error processing {source_file}: {e}")
                    import traceback

                    print(f"Full traceback: {traceback.format_exc()}")
                    # Add basic fallback
                    lines.extend(
                        [
                            "Dataset Overview",
                            "^^^^^^^^^^^^^^^^",
                            "",
                            f"- **Source File**: {source_file}",
                            f"- **Error**: Could not generate full analysis - {e}",
                            "",
                        ]
                    )

            rst_content = "\n".join(lines)

        # Write to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rst_content)
            print(f"Report written to: {output_path}")

        return rst_content

    @staticmethod
    def dataframe_to_rst_table(df: pd.DataFrame) -> List[str]:
        """Convert pandas DataFrame to RST list-table format."""
        if df.empty:
            return ["(No data available)"]

        # Use all available columns - the calling function should provide the right subset
        display_df = df.copy()

        # Format numeric columns
        for col in ["Min Value", "Max Value"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: (
                        f"{x:.2f}"
                        if isinstance(x, (int, float)) and not pd.isna(x)
                        else str(x)
                    )
                )

        lines = []

        # Calculate column widths for formatting - roughly equal widths
        num_cols = len(display_df.columns)
        col_width = max(10, 100 // num_cols)  # At least 10, distribute remaining width

        # Start the list-table directive
        lines.append(".. list-table::")
        lines.append(f"   :widths: {' '.join([str(col_width)] * num_cols)}")
        lines.append("   :header-rows: 1")
        lines.append("")

        # Add header row
        header_row = "   * - " + "\n     - ".join(display_df.columns)
        lines.append(header_row)

        # Add data rows
        for _, row in display_df.iterrows():
            # Clean and escape cell content for RST
            cell_values = []
            for col in display_df.columns:
                cell_value = str(row[col])
                # DON'T escape asterisks - we want bold/italic formatting to work
                # Only escape backticks which could break RST
                cell_value = cell_value.replace("`", "\\`")
                # Replace newlines with spaces to keep content on one line
                cell_value = cell_value.replace("\n", " ").replace("\r", " ")
                cell_values.append(cell_value)

            data_row = "   * - " + "\n     - ".join(cell_values)
            lines.append(data_row)

        lines.append("")
        return lines


class BaseDatasetReport:
    """Base class for dataset analysis results."""

    def __init__(self, dataset_name: str, dataset: xr.Dataset) -> None:
        self.dataset_name = dataset_name
        self.dataset = dataset
        self.analysis_time = datetime.now()

        # Computed properties
        self._statistics = None
        self._temporal_info = None
        self._coordinate_info = None
        self._plot_path = None


class RawDatasetReport(BaseDatasetReport):
    """Report generator for raw (unprocessed) datasets."""

    def __init__(
        self, dataset_name: str, dataset: xr.Dataset, added_attrs: list[str] = None
    ) -> None:
        super().__init__(dataset_name, dataset)
        # Filter out AMOCatlas-added attributes to get truly raw metadata
        if added_attrs:
            self.metadata = {
                k: v for k, v in dataset.attrs.items() if k not in added_attrs
            }
        else:
            self.metadata = dict(dataset.attrs)  # Fallback to all attrs if no tracking

        # Store added attributes for reference
        self.added_attrs = added_attrs or []

        # No variable mapping for raw data
        self._variable_mapping = None


class StandardizedDatasetReport(BaseDatasetReport):
    """Report generator for standardized datasets with variable mapping and metadata tracking."""

    def __init__(
        self, dataset_name: str, dataset: xr.Dataset, attr_changes: dict = None
    ) -> None:
        super().__init__(dataset_name, dataset)
        # Use all metadata (includes AMOCatlas standardization)
        self.metadata = dict(dataset.attrs)

        # Store attribute changes for highlighting
        self.attr_changes = attr_changes or {"added": [], "modified": []}

        # Initialize variable mapping (will be computed lazily)
        self._variable_mapping = None

    @property
    def metadata_changes_summary(self) -> str:
        """Return a summary of metadata changes for display."""
        lines = []
        added = self.attr_changes.get("added", [])
        modified = self.attr_changes.get("modified", [])

        if added:
            lines.append("**Added by AMOCatlas processing:**")
            lines.append("")
            for attr in added:
                # Skip 'files', 'variables', and 'coordinates' attributes
                if attr.lower() in ["files", "variables", "coordinates"]:
                    continue
                value = self.metadata.get(attr, "")
                lines.append(f"- **{attr.replace('_', ' ').title()}**: {value}")
            lines.append("")

        if modified:
            lines.append("**Modified by AMOCatlas processing:**")
            lines.append("")
            for attr in modified:
                # Skip 'files', 'variables', and 'coordinates' attributes
                if attr.lower() in ["files", "variables", "coordinates"]:
                    continue
                value = self.metadata.get(attr, "")
                lines.append(f"- **{attr.replace('_', ' ').title()}**: {value}")
            lines.append("")

        if not added and not modified:
            lines.append("*No metadata modifications detected.*")
            lines.append("")

        return "\n".join(lines)

    @property
    def variable_mapping(self) -> pd.DataFrame:
        """Standardized data may have variable mapping - returns empty DataFrame if none available."""
        if self._variable_mapping is None:
            try:
                self._variable_mapping = self._create_variable_mapping_table()
            except (ValueError, KeyError, TypeError, AttributeError):
                # If mapping fails, return empty DataFrame
                self._variable_mapping = pd.DataFrame()
        return self._variable_mapping

    @property
    def statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if self._statistics is None:
            self._statistics = ReportUtils.compute_dataset_statistics(self.dataset)
        return self._statistics

    @property
    def temporal_info(self) -> Dict[str, Any]:
        """Get temporal coverage information."""
        if self._temporal_info is None:
            self._temporal_info = ReportUtils.analyze_temporal_coverage(self.dataset)
        return self._temporal_info

    @property
    def plot_path(self) -> Optional[str]:
        """Get path to generated plot."""
        if self._plot_path is None:
            self._plot_path = ReportUtils.generate_plot(self.dataset, self.dataset_name)
        return self._plot_path

    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute dataset statistics."""
        stats = {
            "total_variables": len(self.dataset.data_vars),
            "total_coordinates": len(self.dataset.coords),
            "total_attributes": len(self.dataset.attrs),
            "file_size_mb": self.dataset.nbytes / (1024 * 1024),
            "variables": {},
        }

        # Compute statistics for each data variable
        for var_name, var in self.dataset.data_vars.items():
            var_stats = {
                "dtype": str(var.dtype),
                "shape": var.shape,
                "dimensions": list(var.dims),
                "has_time": "time" in var.dims or "TIME" in var.dims,
                "units": var.attrs.get("units", "unknown"),
                "long_name": var.attrs.get("long_name", var_name),
                "missing_data_pct": 0.0,
            }

            # Compute min/max/mean for numeric variables
            if np.issubdtype(var.dtype, np.number):
                # Handle potential NaN values
                valid_data = var.where(np.isfinite(var), drop=True)
                if valid_data.size > 0:
                    var_stats.update(
                        {
                            "min": float(valid_data.min().values),
                            "max": float(valid_data.max().values),
                            "mean": float(valid_data.mean().values),
                            "std": float(valid_data.std().values),
                        }
                    )
                    # Calculate missing data percentage
                    total_size = var.size
                    valid_size = valid_data.size
                    var_stats["missing_data_pct"] = (
                        (total_size - valid_size) / total_size
                    ) * 100

            stats["variables"][var_name] = var_stats

        return stats

    def _create_variable_mapping_table(self) -> pd.DataFrame:
        """Create variable mapping table from metadata."""
        # Use the centralized static method
        return ReportUtils.create_variable_mapping_table(
            self.dataset, self.statistics, self.metadata
        )

    def _create_coordinate_info_table(self) -> pd.DataFrame:
        """Create coordinate information table with original→standardized mapping."""
        return ReportUtils.create_varcoord_table(
            self.dataset, self.statistics, self.metadata, table_type="coordinates"
        )

    @property
    def coordinate_info(self) -> pd.DataFrame:
        """Coordinate information table with mapping information for standardized datasets."""
        if self._coordinate_info is None:
            self._coordinate_info = self._create_coordinate_info_table()
        return self._coordinate_info

    def _analyze_temporal_coverage(self) -> Dict[str, Any]:
        """Analyze temporal coverage of the dataset."""
        # Find time coordinate
        time_coords = []
        for coord_name in self.dataset.coords:
            if coord_name.lower() in ["time", "date"] or "time" in coord_name.lower():
                time_coords.append(coord_name)

        if not time_coords:
            return {"has_time": False}

        time_coord = _select_time_coordinate(self.dataset, time_coords)
        time_data = self.dataset[time_coord]

        # Convert to pandas datetime if needed
        if hasattr(time_data, "to_pandas"):
            time_series = time_data.to_pandas()
        else:
            time_values = time_data.values
            # Handle different time formats
            if hasattr(time_values, "__iter__") and len(time_values) > 0:
                # Check the dtype first
                if str(time_data.dtype).startswith("datetime64"):
                    # Already datetime64, just convert to pandas
                    time_series = pd.to_datetime(time_values)
                else:
                    # Check for YYYYMM format first
                    units = time_data.attrs.get("units", "").upper()
                    if units == "YYYYMM" or (
                        len(time_values) > 0
                        and isinstance(time_values[0], (int, np.integer))
                        and 190000 <= time_values[0] <= 300000
                    ):
                        # Handle YYYYMM format
                        time_series = ReportUtils.handle_yyyymm_time_format(time_data)
                    else:
                        # Numeric values - check if they look like seconds since 1970
                        try:
                            sample_val = float(time_values[0])
                            if sample_val > 1e9:  # Likely seconds since 1970
                                time_series = pd.to_datetime(time_values, unit="s")
                            else:
                                time_series = pd.to_datetime(time_values)
                        except (ValueError, TypeError):
                            time_series = pd.to_datetime(time_values)
            else:
                time_series = pd.to_datetime(time_values)

        # Remove invalid times and extreme outliers
        valid_times = time_series.dropna()

        # Filter out extremely unrealistic dates (e.g., from sentinel values)
        # Keep only dates between 1900 and 2100 (reasonable range for oceanographic data)
        try:
            min_year = pd.Timestamp("1900-01-01")
            max_year = pd.Timestamp("2100-01-01")
            valid_times = valid_times[
                (valid_times >= min_year) & (valid_times <= max_year)
            ]
        except (TypeError, ValueError):
            # If date filtering fails, just keep the dropna() result
            pass

        if len(valid_times) == 0:
            return {"has_time": True, "valid_times": False}

        # Calculate temporal statistics
        start_date = valid_times.min()
        end_date = valid_times.max()

        time_info = {
            "has_time": True,
            "valid_times": True,
            "coordinate_name": time_coord,
            "start_date": start_date,
            "end_date": end_date,
            "total_records": len(valid_times),
            "time_span_days": ReportUtils.safe_time_diff_days(end_date, start_date),
            "time_span_years": ReportUtils.safe_time_diff_days(end_date, start_date)
            / 365.25,
        }

        # Estimate sampling frequency
        if len(valid_times) > 1:
            time_diffs = valid_times.diff().dropna()
            median_diff = time_diffs.median()
            time_info["median_sampling_interval"] = median_diff
            time_info["estimated_frequency"] = self._estimate_frequency(median_diff)

        return time_info

    def _estimate_frequency(self, median_diff: pd.Timedelta) -> str:
        """Estimate sampling frequency from median time difference."""
        hours = median_diff.total_seconds() / 3600

        if hours < 1:
            return f"{int(median_diff.total_seconds() // 60)}min"
        elif hours < 12:
            return f"{hours:.1f}H"
        elif 10 <= hours <= 14:
            return "12H"
        elif 20 <= hours <= 28:
            return "daily"
        elif 28 <= hours <= 35:
            return "monthly"
        elif 720 <= hours <= 760:  # ~30-31 days
            return "monthly"
        elif 2000 <= hours <= 2300:  # ~3 months (quarterly)
            return "3-monthly"
        elif 4000 <= hours <= 4500:  # ~6 months
            return "6-monthly"
        elif 8000 <= hours <= 9000:  # ~12 months (annual)
            return "annual"
        else:
            return f"{hours:.1f}H"

    def _generate_plot(self) -> Optional[str]:
        """Generate a plot for the dataset and return the path."""
        try:
            plots_dir = _reports_plots_dir()

            # Generate plot filename
            plot_filename = (
                f"{self.dataset_name.replace(' ', '_').lower()}_timeseries.png"
            )
            plot_path = plots_dir / plot_filename

            # Try to find a suitable variable for plotting (prefer MOC variables)
            moc_vars = [var for var in self.dataset.data_vars if "moc" in var.lower()]
            if moc_vars:
                var_to_plot = moc_vars[0]
            else:
                # Fall back to first variable
                var_to_plot = list(self.dataset.data_vars)[0]

            # Use plotters to create the plot without monthly resampling
            # Figure size: 2/3rds as wide, maintaining aspect ratio
            title = f"{self.dataset_name.upper()} Time Series"
            fig, ax = plotters.plot_amoc_timeseries(
                self.dataset,
                varnames=[var_to_plot],
                title=title,
                resample_monthly=False,
                plot_raw=True,
                figsize=(7, 2.5),  # Slightly wider figure
            )

            # Turn off legend and save the plot (suppress matplotlib metadata for deterministic output)
            ax = fig.get_axes()[0]
            ax.legend().set_visible(False)
            fig.savefig(
                plot_path,
                dpi=150,
                bbox_inches="tight",
                metadata={"Software": None, "Creation Time": None},
            )
            plt.close(fig)

            # Return relative path for Sphinx (from reports directory)
            plot_path_return = f"../_static/reports/{plot_filename}"

        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            OSError,
            IOError,
            ImportError,
        ) as e:
            log_debug(f"Failed to generate plot for {self.dataset_name}: {e}")
            return None

        else:
            return plot_path_return


def analyze_standardized_dataset(
    dataset_name: str,
    transport_only: bool = True,
    all_files: bool = False,  # noqa: ARG001
    dataset_index: int = 0,  # noqa: ARG001
) -> Union[StandardizedDatasetReport, List[StandardizedDatasetReport]]:
    """Analyze a standardized dataset and return report data with metadata tracking.

    Parameters
    ----------
    dataset_name : str
        Name of the dataset (e.g., "rapid", "move")
    transport_only : bool, optional
        Whether to load transport-only data, by default True
    all_files : bool, optional
        Whether to load all available files for the dataset, by default False
    dataset_index : int, optional
        Index of dataset to analyze when multiple files available, by default 0

    Returns
    -------
    StandardizedDatasetReport
        Analysis results with variable mapping and metadata tracking

    Examples
    --------
    >>> report_data = analyze_standardized_dataset("rapid", transport_only=True)
    >>> print(f"Dataset has {report_data.statistics['total_variables']} variables")
    >>> print(f"Added attributes: {report_data.attr_changes['added']}")

    """
    from amocatlas import read

    # Get the read function for this dataset
    read_func = getattr(read, dataset_name.lower())

    # Load standardized data with attribute tracking
    dataset, attr_changes = read_func(
        transport_only=transport_only,
        raw=False,  # Get standardized data
        track_added_attrs=True,
    )

    return StandardizedDatasetReport(dataset_name, dataset, attr_changes)


def analyze_dataset(
    dataset_name: str, transport_only: bool = True, dataset_index: int = 0
) -> RawDatasetReport:
    """Analyze a dataset and return report data.

    Parameters
    ----------
    dataset_name : str
        Name of the dataset (e.g., "rapid26n", "move16n")
    transport_only : bool, optional
        Whether to load transport-only data, by default True
    dataset_index : int, optional
        Index of dataset to analyze when multiple files available, by default 0

    Returns
    -------
    DatasetReport
        Analysis results

    Examples
    --------
    >>> report_data = analyze_dataset("rapid26n", transport_only=True)
    >>> print(f"Dataset has {report_data.statistics['total_variables']} variables")
    >>> # Analyze second RAPID dataset
    >>> report_data = analyze_dataset("rapid", transport_only=False, dataset_index=1)

    """
    log_info(f"Analyzing dataset: {dataset_name}")

    # Load the dataset using the read API
    read_func = getattr(
        read,
        dataset_name.replace("26n", "")
        .replace("16n", "")
        .replace("34s", "")
        .replace("55n", "")
        .replace("47n", "noac47n")
        .replace("41n", "wh41n"),
    )

    # Load dataset with standardization applied and track added attributes
    result = read_func(transport_only=transport_only, track_added_attrs=True)

    # Extract datasets (metadata changes are now embedded in dataset attributes)
    if isinstance(result, list):
        datasets = result
    else:
        datasets = [result]

    # Check dataset index
    if dataset_index >= len(datasets):
        raise ValueError(
            f"Dataset index {dataset_index} out of range. Available datasets: 0-{len(datasets) - 1}"
        )

    # Get the requested dataset and extract its metadata changes
    dataset = datasets[dataset_index]
    added_attrs = dataset.attrs.pop(
        "_amocatlas_metadata_changes", {"added": [], "modified": []}
    )

    log_debug(
        f"Loaded dataset with {len(dataset.data_vars)} variables, {len(added_attrs)} attributes added by AMOCatlas"
    )

    return RawDatasetReport(dataset_name, dataset, added_attrs)


def generate_dataset_report(
    dataset_name: str,
    transport_only: bool = True,
    output_format: str = "rst",
    dataset_index: int = 0,
) -> str:
    """Generate a dataset report.

    Parameters
    ----------
    dataset_name : str
        Name of the dataset to report on
    transport_only : bool, optional
        Whether to analyze transport-only data, by default True
    output_format : str, optional
        Output format ("rst", "markdown", "html"), by default "rst"
    dataset_index : int, optional
        Index of dataset to analyze when multiple files available, by default 0

    Returns
    -------
    str
        Generated report in the specified format

    Notes
    -----
    This function uses track_added_attrs=True internally to track which metadata
    attributes were added during data loading. The '_amocatlas_metadata_changes'
    attribute is temporarily embedded in the dataset and extracted/removed during
    the analysis phase.

    """
    # Analyze the standardized dataset (with variable mapping and metadata tracking)
    report_data = analyze_standardized_dataset(
        dataset_name, transport_only=transport_only, dataset_index=dataset_index
    )

    if output_format.lower() == "rst":
        return _generate_rst_report(report_data)
    else:
        raise NotImplementedError(
            f"Output format '{output_format}' not yet implemented"
        )


def _generate_rst_report(
    report_data: BaseDatasetReport, skip_source_header: bool = False
) -> str:
    """Generate RST-formatted report.

    Parameters
    ----------
    report_data : BaseDatasetReport
        Report data to format
    skip_source_header : bool, optional
        If True, skip adding the source file header (for multi-dataset reports)

    """
    dataset_name = report_data.dataset_name
    stats = report_data.statistics
    temporal = report_data.temporal_info
    mapping_df = report_data.variable_mapping
    coordinate_df = report_data.coordinate_info
    # Use regular metadata for display
    metadata = report_data.metadata if hasattr(report_data, "metadata") else {}

    # Build the RST content
    lines = []

    # Title
    title = f"{dataset_name.upper()} Datasets"
    lines.extend(
        [
            title,
            "=" * len(title),
            "",
        ]
    )

    # Source file as level 2 header (skip if requested). No leading "----": this is the
    # first section, and a document may not begin with a transition.
    if not skip_source_header:
        source_file = report_data.dataset.attrs.get("source_file", "Unknown source")
        lines.extend(
            [
                source_file,
                "-" * len(source_file),
                "",
            ]
        )

    # Dataset Overview
    lines.extend(
        [
            "Dataset Overview",
            "^^^^^^^^^^^^^^^^",
            "",
        ]
    )

    # Use case-insensitive lookup for common fields (metadata is standardized dataset attributes)
    def get_field(field_name: str, default: str = "Unknown") -> str:
        if not metadata:
            return default
        # Try exact match first
        if field_name in metadata:
            return metadata[field_name]
        # Try capitalized version
        cap_field = field_name.capitalize()
        if cap_field in metadata:
            return metadata[cap_field]
        # Try title case version
        title_field = field_name.replace("_", " ").title().replace(" ", "_")
        if title_field in metadata:
            return metadata[title_field]
        return default

    # Store citation and acknowledgement for later display
    citation_for_later = get_field("citation")
    # Check both spellings of acknowledgment/acknowledgement
    acknowledgement_for_later = None
    if get_field("acknowledgement", None) is not None:
        acknowledgement_for_later = get_field("acknowledgement")
    elif get_field("acknowledgment", None) is not None:
        acknowledgement_for_later = get_field("acknowledgment")
    else:
        acknowledgement_for_later = "Unknown"

    if metadata:
        lines.extend(
            [
                f"- **Project**: {get_field('project')}",
                f"- **Description**: {get_field('description', 'No description available')}",
            ]
        )

        # Website field - try multiple variations
        website = get_field("website") or get_field("weblink") or get_field("web_link")
        if website and website != "Unknown":
            lines.append(f"- **Website**: {website}")

        # DOI field - try multiple variations
        doi = get_field("doi") or get_field("DOI")
        if doi and doi != "Unknown":
            # Make DOI clickable if it's not already a URL
            if not doi.startswith("http"):
                if doi.startswith("doi:"):
                    doi_code = doi.replace("doi:", "").strip()
                else:
                    doi_code = doi
                doi_url = f"http://doi.org/{doi_code}"
            else:
                doi_url = doi
            lines.append(f"- **DOI**: {doi_url}")

    # Add source file information from dataset attributes
    if hasattr(report_data.dataset, "attrs"):
        attrs = report_data.dataset.attrs
        if attrs.get("source_file"):
            lines.append(f"- **Source File**: {attrs['source_file']}")
        if attrs.get("data_product"):
            lines.append(f"- **Data Product**: {attrs['data_product']}")
        license_value = attrs.get("license", "")
        if license_value and license_value.lower() != "void":
            lines.append(f"- **License**: {license_value}")
        else:  # If empty, "void", or missing - always show empty license field
            lines.append("- **License**: ")

        # Add date created if available
        date_created = (
            get_field("date_created")
            or get_field("creation_date")
            or get_field("created")
        )
        if date_created and date_created != "Unknown":
            lines.append(f"- **Date Created**: {date_created}")

    # Temporal Coverage
    if temporal.get("has_time") and temporal.get("valid_times"):
        lines.extend(
            [
                f"- **Time Coverage**: {ReportUtils.safe_format_date(temporal['start_date'])} to {ReportUtils.safe_format_date(temporal['end_date'])}",
                f"- **Record Length**: {temporal['total_records']:,} observations ({temporal['time_span_years']:.1f} years)",
            ]
        )

        if "estimated_frequency" in temporal:
            lines.append(f"- **Sampling Frequency**: {temporal['estimated_frequency']}")

    # Add distribution statement if available (after overview, before citation)
    distribution_statement = (
        get_field("distribution_statement")
        or get_field("distribution")
        or get_field("access_constraints")
    )
    if distribution_statement and distribution_statement != "Unknown":
        lines.extend(
            ["", "**Distribution Statement:**", "", f"    {distribution_statement}", ""]
        )

    # Add citation and acknowledgement if available (from standardized dataset attributes)
    citation_to_display = citation_for_later
    acknowledgement_to_display = acknowledgement_for_later

    if citation_to_display and citation_to_display != "Unknown":
        # Make DOI clickable if present
        import re

        doi_pattern = r"doi:\s*([0-9]+\.[0-9]+/[^\s]+)"
        doi_match = re.search(doi_pattern, citation_to_display)

        if doi_match:
            doi = doi_match.group(1)
            doi_url = f"http://doi.org/{doi}"
            citation_to_display = re.sub(
                doi_pattern, f"doi: {doi_url}", citation_to_display
            )

        lines.extend(
            [
                "",
                "**Citation:**",
                "",
                f"    {citation_to_display}",
            ]
        )

    if acknowledgement_to_display and acknowledgement_to_display != "Unknown":
        lines.extend(
            [
                "",
                "**Acknowledgement:**",
                "",
                f"    {acknowledgement_to_display}",
            ]
        )

    lines.append("")

    # Add plot if available
    plot_path = report_data.plot_path
    if plot_path:
        lines.extend(
            [
                "Dataset Visualization",
                "^^^^^^^^^^^^^^^^^^^^^",
                "",
                f".. figure:: {plot_path}",
                "   :alt: AMOC time series plot",
                "   :align: center",
                "   :scale: 80%",
                "",
                f"   Time series plot for {dataset_name.upper()} dataset.",
                "",
            ]
        )

    # Dataset Statistics
    lines.extend(
        [
            "Dataset Statistics",
            "^^^^^^^^^^^^^^^^^^",
            "",
            f"- **Total Variables**: {stats['total_variables']}",
            f"- **Total Coordinates**: {stats['total_coordinates']}",
            f"- **Dataset Size**: {stats['file_size_mb']:.2f} MB",
            "",
        ]
    )

    # Coordinate Information
    lines.extend(
        [
            "Coordinate Information",
            "^^^^^^^^^^^^^^^^^^^^^^",
            "",
            "The following table shows information about the dataset coordinates in the standardised version, including coordinate name remapping from the original, if any:",
            "",
        ]
    )

    if not coordinate_df.empty:
        coord_key_columns = [
            "Coordinate",
            "Description",
            "Units",
            "Size",
            "Min Value",
            "Max Value",
            "Missing %",
        ]
        coord_display_df = coordinate_df[coord_key_columns].copy()
        lines.extend(ReportUtils.dataframe_to_rst_table(coord_display_df))
    else:
        lines.append("No coordinate information available.")

    lines.append("")

    # Variable Information Table
    lines.extend(
        [
            "Variable Information",
            "^^^^^^^^^^^^^^^^^^^^",
            "",
            "The following table shows the mapping from original variable names to standardized names,",
            "along with key statistics for each variable.",
            "",
        ]
    )

    # Generate RST table for variables
    if not mapping_df.empty:
        var_key_columns = [
            "Variable",
            "Description",
            "Units",
            "Size",
            "Min Value",
            "Max Value",
            "Missing %",
        ]
        var_display_df = mapping_df[var_key_columns].copy()
        lines.extend(ReportUtils.dataframe_to_rst_table(var_display_df))
    else:
        lines.append("No variable mapping information available.")

    lines.append("")

    # Complete Metadata
    _meta_title = "Metadata (edits applied noted)"
    lines.extend(
        [
            _meta_title,
            "^" * len(_meta_title),
            "",
            "The following metadata describes this dataset:",
            "",
        ]
    )

    # Display all metadata in structured format, but filter out verbose sections
    excluded_keys = [
        "citation",
        "files",
        "variables",
        "coordinates",
    ]  # Skip verbose metadata

    # Get information about which attributes were modified by AMOCatlas, if available
    added_attrs = set()
    modified_attrs = set()
    if isinstance(report_data, StandardizedDatasetReport):
        added_attrs = set(report_data.attr_changes.get("added", []))
        modified_attrs = set(report_data.attr_changes.get("modified", []))

    for key, value in metadata.items():
        if key not in excluded_keys:
            # Preserve exact case for case-sensitive attributes
            if key in ["Conventions", "featureType", "featureType_vocabulary"]:
                formatted_key = key  # Keep exact case and formatting
            else:
                formatted_key = key.replace("_", " ").title()

            # Update time coverage with actual dataset values if available
            if (
                key in ["time_coverage_start", "time_coverage_end"]
                and temporal.get("has_time")
                and temporal.get("valid_times")
            ):
                if key == "time_coverage_start":
                    value = ReportUtils.safe_format_date(temporal["start_date"])
                elif key == "time_coverage_end":
                    value = ReportUtils.safe_format_date(temporal["end_date"])

            # Add annotation if this field was edited by AMOCatlas
            annotation = ""
            if key in added_attrs or key in modified_attrs:
                annotation = r"\*"

            if isinstance(value, (list, tuple)):
                lines.append(
                    f"- **{formatted_key}{annotation}**: {', '.join(map(str, value))}"
                )
            elif isinstance(value, dict):
                # Skip large dictionary dumps
                if len(str(value)) > 200:
                    lines.append(
                        f"- **{formatted_key}{annotation}**: [Complex metadata structure - {len(value)} items]"
                    )
                else:
                    lines.append(f"- **{formatted_key}{annotation}**: {str(value)}")
            else:
                # Make DOI clickable if it's a DOI field
                if (
                    key.lower() in ["doi", "digital_object_identifier"]
                    and str(value).strip()
                ):
                    doi_value = str(value).strip()
                    if doi_value.startswith("http"):
                        # Already a URL
                        lines.append(f"- **{formatted_key}{annotation}**: {doi_value}")
                    else:
                        # Convert to clickable URL
                        if doi_value.startswith("doi:"):
                            doi_value = doi_value[4:].strip()
                        elif doi_value.startswith("10."):
                            pass  # Already just the DOI part
                        lines.append(
                            f"- **{formatted_key}{annotation}**: https://doi.org/{doi_value}"
                        )
                else:
                    lines.append(f"- **{formatted_key}{annotation}**: {value}")

    lines.append("")

    return "\n".join(lines)


def _dataframe_to_rst_table(df: pd.DataFrame) -> List[str]:
    """Convert pandas DataFrame to RST table format."""
    if df.empty:
        return ["(No data available)"]

    # Use all available columns - the calling function should provide the right subset
    display_df = df.copy()

    # Format numeric columns
    for col in ["Min Value", "Max Value"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: (
                    f"{x:.2f}"
                    if isinstance(x, (int, float)) and not pd.isna(x)
                    else str(x)
                )
            )

    lines = []

    # Calculate column widths
    col_widths = {}
    for col in display_df.columns:
        col_widths[col] = max(
            len(str(col)),
            (
                display_df[col].astype(str).str.len().max()
                if not display_df[col].empty
                else 0
            ),
        )

    # Create header separator
    header_sep = (
        "+" + "+".join("-" * (col_widths[col] + 2) for col in display_df.columns) + "+"
    )

    # Add table
    lines.append(header_sep)

    # Add header row
    header_row = (
        "|"
        + "|".join(f" {col:<{col_widths[col]}} " for col in display_df.columns)
        + "|"
    )
    lines.append(header_row)

    # Add header separator
    header_sep2 = (
        "+" + "+".join("=" * (col_widths[col] + 2) for col in display_df.columns) + "+"
    )
    lines.append(header_sep2)

    # Add data rows
    for _, row in display_df.iterrows():
        data_row = (
            "|"
            + "|".join(
                f" {str(row[col]):<{col_widths[col]}} " for col in display_df.columns
            )
            + "|"
        )
        lines.append(data_row)
        lines.append(header_sep)

    lines.append("")
    return lines


def rapid(all_files: bool = True, output_file: str = None) -> str:
    """Generate a RAPID dataset report.

    Parameters
    ----------
    all_files : bool, optional
        Whether to include all RAPID files in the report, by default True
    output_file : str, optional
        Path to write the RST report. If None, returns RST content as string.

    Returns
    -------
    str
        RST content of the report

    Examples
    --------
    >>> from amocatlas import report
    >>> rst_content = report.rapid()  # Generate report for all RAPID files
    >>> rst_content = report.rapid(all_files=False)  # Only transport file

    """
    return ReportUtils.generate_array_report(
        "rapid", all_files=all_files, output_file=output_file
    )


def osnap(all_files: bool = True, output_file: str = None) -> str:
    """Generate an OSNAP dataset report."""
    return ReportUtils.generate_array_report(
        "osnap", all_files=all_files, output_file=output_file
    )


def move(all_files: bool = True, output_file: str = None) -> str:
    """Generate a MOVE dataset report."""
    return ReportUtils.generate_array_report(
        "move", all_files=all_files, output_file=output_file
    )


def samba(all_files: bool = True, output_file: str = None) -> str:
    """Generate a SAMBA dataset report."""
    return ReportUtils.generate_array_report(
        "samba", all_files=all_files, output_file=output_file
    )


def all(
    arrays: List[str] = None, output_dir: str = "docs/source/reports"
) -> Dict[str, str]:
    """Generate reports for all available arrays.

    Parameters
    ----------
    arrays : list of str, optional
        List of array names to generate reports for. If None, generates reports for all available arrays.
    output_dir : str, optional
        Directory to write report files to, by default "docs/source/reports"

    Returns
    -------
    dict
        Dictionary mapping array names to their RST report content

    Examples
    --------
    >>> from amocatlas import report
    >>> reports = report.all()  # Generate reports for all arrays
    >>> reports = report.all(['rapid', 'osnap'])  # Only specific arrays

    """
    if arrays is None:
        # List of all available arrays (matching the ReaderUtils datasource mapping)
        arrays = ["rapid", "osnap", "move", "samba", "mocha", "fw2015", "wh41n", "dso"]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    reports = {}
    print(f"Generating reports for {len(arrays)} arrays...")

    for array_name in arrays:
        try:
            print(f"\nGenerating {array_name.upper()} report...")

            # Generate report
            rst_content = ReportUtils.generate_array_report(array_name, all_files=True)
            reports[array_name] = rst_content

            # Write to file
            output_file = output_path / f"{array_name}_report.rst"
            output_file.write_text(rst_content)
            print(f"Written: {output_file}")

        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            OSError,
            IOError,
            PermissionError,
        ) as e:
            print(f"Failed to generate report for {array_name}: {e}")
            reports[array_name] = f"Error: {e}"

    print(
        f"\nGenerated {len([r for r in reports.values() if not r.startswith('Error:')])} reports successfully"
    )
    return reports


# Example usage and testing
if __name__ == "__main__":
    # Test with RAPID dataset
    print("Generating RAPID dataset report...")
    report = generate_dataset_report("rapid", transport_only=True)
    print(report[:500] + "..." if len(report) > 500 else report)
