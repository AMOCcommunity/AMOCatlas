"""AMOCatlas AC1 Format Compliance Checker.

This module provides validation for transport data files converted to AC1 format
following the OceanSITES/AC1 specification.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import xarray as xr


@dataclass
class ValidationResult:
    """Container for validation results."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    file_type: str | None = None


# Generic AC1 compliance specifications
GENERIC_SPECS = {
    # Approved UDUNITS-2 units by standard_name
    "approved_units_by_standard_name": {
        # Time and coordinates
        "time": "seconds since 1970-01-01T00:00:00Z",
        "latitude": "degree_north",
        "longitude": "degree_east",
        "depth": "m",
        # Temperature
        "sea_water_temperature": "degree_Celsius",
        "sea_water_conservative_temperature": "degree_Celsius",
        "sea_water_potential_temperature": "degree_Celsius",
        # Salinity
        "sea_water_practical_salinity": "1",  # or 'psu'
        "sea_water_absolute_salinity": "g kg-1",
        "sea_water_reference_salinity": "g kg-1",
        # Pressure and density
        "sea_water_pressure": "dbar",
        "sea_water_sigma_theta": "kg m-3",
        "sea_water_sigma_t": "kg m-3",
        # Velocity
        "northward_sea_water_velocity": "m s-1",
        "eastward_sea_water_velocity": "m s-1",
        "upward_sea_water_velocity": "m s-1",
        # Transports and streamfunction
        "ocean_volume_transport_across_line": "sverdrup",
        "northward_ocean_heat_transport": "petawatt",
        # northward_ocean_freshwater_transport intentionally omitted: AMOCatlas reports
        # freshwater transport in sverdrup (a volume flux), which is not convertible to
        # the CF canonical units kg s-1 (a mass flux). Rather than change the reported
        # values, the standard_name is dropped (carried instead in long_name + a comment
        # naming the reference density), so there is no CF units expectation to check here.
        "ocean_meridional_overturning_streamfunction": "sverdrup",
        # Additional oceanographic variables
        "sea_water_potential_density": "kg m-3",
        "sea_water_potential_density_anomaly": "kg m-3",
        "barotropic_eastward_sea_water_velocity": "m s-1",
        "barotropic_northward_sea_water_velocity": "m s-1",
    },
    # Alternative units that are acceptable for certain standard names
    "alternative_units": {
        "sea_water_practical_salinity": ["1", "psu"],  # Both are acceptable
        "sea_water_pressure": ["dbar", "Pa"],  # Both pressure units acceptable
    },
    # Required vocabularies
    "required_vocabularies": {
        "sea_water_temperature": "https://vocab.nerc.ac.uk/collection/P07/current/CFSN0335/",
        "sea_water_practical_salinity": "http://vocab.nerc.ac.uk/collection/P07/current/IADIHDIJ/",
        "northward_sea_water_velocity": "http://vocab.nerc.ac.uk/collection/P07/current/CFSN0494/",
        "ocean_volume_transport_across_line": "http://vocab.nerc.ac.uk/collection/P07/current/W946809H/",
        "northward_ocean_heat_transport": "http://vocab.nerc.ac.uk/collection/P07/current/CFSN0483/",
        "northward_ocean_freshwater_transport": "http://vocab.nerc.ac.uk/collection/P07/current/CFSN0507/",
        "ocean_meridional_overturning_streamfunction": "https://vocab.nerc.ac.uk/collection/P07/current/CFSN0466/",
        "sea_water_pressure": "https://vocab.nerc.ac.uk/collection/P07/current/CFSN0330/",
        "sea_water_sigma_theta": "http://vocab.nerc.ac.uk/collection/P07/current/CFSN0333/",
    },
    # Required global attributes (generic AC1)
    "required_global_attrs": [
        "Conventions",
        "format_version",
        "data_type",
        "featureType",
        "data_mode",
        "title",
        "summary",
        "source",
        "site_code",
        "array",
        "geospatial_lat_min",
        "geospatial_lat_max",
        "geospatial_lon_min",
        "geospatial_lon_max",
        "time_coverage_start",
        "time_coverage_end",
        "contributor_name",
        "contributor_role",
        "contributor_role_vocabulary",
        "contributor_id",
        "contributing_institutions",
        "contributing_institutions_vocabulary",
        "contributing_institutions_role",
        "contributing_institutions_role_vocabulary",
        "source_acknowledgement",
        # Additional mandatory OceanSITES attributes
        "platform_code",
        "naming_authority",
        "id",
        "cdm_data_type",
        "QC_indicator",
        "processing_level",
        "date_created",
        "institution",
    ],
    # Required conventions
    "required_conventions": ["CF-1.8", "OceanSITES-1.4", "ACDD-1.3"],
    # Coordinate specifications
    "coordinate_specs": {
        "TIME": {"axis": "T", "required": True},
        "LATITUDE": {"axis": "Y", "units": "degree_north", "range": (-90, 90)},
        "LONGITUDE": {"axis": "X", "units": "degree_east", "range": (-180, 360)},
        "DEPTH": {"axis": "Z", "units": "m", "positive_down_range": (0, float("inf"))},
        "PRESSURE": {"axis": "Z", "units": "dbar", "range": (0, float("inf"))},
    },
    # General OceanSITES filename pattern
    "general_filename_pattern": r"^OS_([A-Z0-9]+)_(\d{8})-(\d{8})_([A-Z]{3})_([A-Za-z0-9_T]+)\.nc$",
    # Valid content types
    "valid_content_types": ["LTS", "GRD", "DPR"],
}

# RAPID-specific specifications
RAPID_SPECS = {
    # File type patterns (more specific than general pattern)
    "file_patterns": {
        "component_transports": r"^OS_RAPID_(\d{8})-(\d{8})_DPR_transports_T12H\.nc$",
        "meridional_transports": r"^OS_RAPID_(\d{8})-(\d{8})_DPR_transports_T10D\.nc$",
        "streamfunction": r"^OS_RAPID_(\d{8})-(\d{8})_DPR_streamfunction_T12H\.nc$",
        "gridded_sections": r"^OS_RAPID_(\d{8})-(\d{8})_GRD_sections_T10D\.nc$",
        "gridded_moorings": r"^OS_RAPID_(\d{8})-(\d{8})_GRD_gridded_mooring\.nc$",
    },
    # Array-specific attributes
    "site_code": "RAPID",
    "array": "RAPID",
    "data_mode": "D",
    # File-specific requirements
    "file_requirements": {
        "component_transports": {
            "dimensions": {"N_COMPONENT": 8},
            "required_variables": [
                "TRANSPORT",
                "MOC_TRANSPORT",
                "TRANSPORT_NAME",
                "TRANSPORT_DESCRIPTION",
            ],
        },
        "meridional_transports": {
            "dimensions": {"DEPTH": 307, "SIGMA0": 631},
            "required_variables": [
                "MOC_TRANSPORT_DEPTH",
                "MOC_TRANSPORT_SIGMA",
                "HEAT_TRANSPORT",
                "FRESHWATER_TRANSPORT",
                "STREAMFUNCTION_DEPTH",
                "STREAMFUNCTION_SIGMA",
            ],
        },
        "streamfunction": {
            "dimensions": {"DEPTH": 307},
            "forbidden_dimensions": ["SIGMA0"],
            "required_variables": ["STREAMFUNCTION"],
        },
        "gridded_sections": {
            "dimensions": {"DEPTH": 307},
            "required_variables": ["TEMPERATURE", "SALINITY", "VELOCITY"],
        },
        "gridded_moorings": {
            "dimensions": {"N_PROF": 5, "N_LEVELS": 242},
            "required_variables": ["TEMPERATURE", "SALINITY"],
        },
    },
}


class AC1ComplianceChecker:
    """Compliance checker for AMOCatlas AC1 format files.

    Validates data files against generic AC1 specification and array-specific requirements.
    Separated into generic compliance tests (required for all AC1 files) and
    array-specific tests (specific to individual observing arrays).
    """

    def __init__(self, array_specs: dict = None) -> None:
        """Initialize the compliance checker.

        Parameters
        ----------
        array_specs : dict, optional
            Array-specific specifications. Defaults to RAPID_SPECS.

        """
        self.array_specs = array_specs if array_specs is not None else RAPID_SPECS
        self.generic_specs = GENERIC_SPECS

    def validate_file(self, filepath: str) -> ValidationResult:
        """Validate a file against AC1 format specification.

        Parameters
        ----------
        filepath : str
            Path to the NetCDF file to validate

        Returns
        -------
        ValidationResult
            Validation results with errors and warnings

        """
        result = ValidationResult(passed=True)

        try:
            # Validate filename
            file_type = self._validate_filename(filepath, result)
            result.file_type = file_type

            if not file_type:
                result.passed = False
                return result

            # Load dataset
            try:
                ds = xr.open_dataset(filepath)
            except (OSError, ValueError, KeyError) as e:
                result.errors.append(f"Failed to open NetCDF file: {e}")
                result.passed = False
                return result

            # Run validation checks
            self._validate_dimensions(ds, file_type, result)
            self._validate_variables(ds, file_type, result)
            self._validate_global_attributes(ds, result)
            self._validate_data_values(ds, filepath, result)

            ds.close()

        except (OSError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            result.errors.append(f"Unexpected error during validation: {e}")
            result.passed = False

        # Set overall pass/fail
        result.passed = len(result.errors) == 0

        return result

    def _validate_filename(self, filepath: str, result: ValidationResult) -> str | None:
        """Validate filename against OceanSITES convention."""
        filename = Path(filepath).name

        # Check general OceanSITES pattern first
        general_match = re.match(
            self.generic_specs["general_filename_pattern"], filename
        )
        if not general_match:
            result.errors.append(
                "Filename must follow OceanSITES pattern: OS_[PSPANCode]_[StartEndCode]_[ContentType]_[PARTX].nc"
            )
            return None

        # Extract components
        pspan_code, start_date, end_date, content_type, partx = general_match.groups()

        # Validate PSPANCode matches array
        if pspan_code != self.array_specs["site_code"]:
            result.errors.append(
                f"PSPANCode must be '{self.array_specs['site_code']}' for {self.array_specs['site_code']} data, got '{pspan_code}'"
            )
            return None

        # Validate ContentType
        if content_type not in self.generic_specs["valid_content_types"]:
            result.errors.append(
                f"ContentType must be one of {self.generic_specs['valid_content_types']}, got '{content_type}'"
            )
            return None

        # Validate date format and range
        try:
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")

            if start_dt > end_dt:
                result.errors.append(
                    f"Start date ({start_date}) must be <= end date ({end_date})"
                )
        except ValueError as e:
            result.errors.append(f"Invalid date format in filename: {e}")
            return None

        # Try to determine specific file type from array patterns
        file_type = None
        for ftype, pattern in self.array_specs["file_patterns"].items():
            if re.match(pattern, filename):
                file_type = ftype
                break

        if not file_type:
            # If no specific pattern matches, create a generic type based on content
            file_type = f"{content_type.lower()}_{partx.lower()}"
            result.warnings.append(
                f"Using generic file type '{file_type}' - no specific pattern matched"
            )

        return file_type

    def _validate_dimensions(
        self, ds: xr.Dataset, file_type: str, result: ValidationResult
    ) -> None:
        """Validate dimensions according to generic and file-specific requirements."""
        # Generic dimension checks
        self._validate_generic_dimensions(ds, result)

        # Array-specific dimension checks
        self._validate_array_specific_dimensions(ds, file_type, result)

        # Check dimension ordering (T, Z, Y, X with components leftmost)
        self._validate_dimension_ordering(ds, result)

    def _validate_generic_dimensions(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate generic dimension requirements."""
        # TIME dimension is always required
        if "TIME" not in ds.sizes:
            result.errors.append("TIME dimension is required")
        else:
            if ds.sizes["TIME"] != len(ds.TIME):
                result.warnings.append("TIME dimension should be unlimited")

    def _validate_array_specific_dimensions(
        self, ds: xr.Dataset, file_type: str, result: ValidationResult
    ) -> None:
        """Validate array-specific dimension requirements."""
        if file_type not in self.array_specs["file_requirements"]:
            return

        requirements = self.array_specs["file_requirements"][file_type]

        # Check required dimensions with specific sizes
        if "dimensions" in requirements:
            for dim_name, expected_size in requirements["dimensions"].items():
                if dim_name not in ds.sizes:
                    result.errors.append(
                        f"{dim_name} dimension required for {file_type}"
                    )
                elif ds.sizes[dim_name] != expected_size:
                    result.errors.append(
                        f"{dim_name} must be {expected_size}, got {ds.sizes[dim_name]}"
                    )

        # Check forbidden dimensions
        if "forbidden_dimensions" in requirements:
            for dim_name in requirements["forbidden_dimensions"]:
                if dim_name in ds.dims:
                    result.errors.append(
                        f"{dim_name} dimension should NOT be present in {file_type} files"
                    )

    def _validate_dimension_ordering(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate CF convention dimension ordering."""
        for var_name, var in ds.data_vars.items():
            dims = var.dims

            if len(dims) <= 1:
                continue

            # Check for proper ordering
            t_idx = z_idx = y_idx = x_idx = comp_idx = -1

            for i, dim in enumerate(dims):
                if dim == "TIME":
                    t_idx = i
                elif dim in ["DEPTH", "PRESSURE", "SIGMA0"]:
                    z_idx = i
                elif dim == "LATITUDE":
                    y_idx = i
                elif dim == "LONGITUDE":
                    x_idx = i
                elif dim == "N_COMPONENT":
                    comp_idx = i

            # Component dimensions should be leftmost
            if comp_idx >= 0:
                for idx in [t_idx, z_idx, y_idx, x_idx]:
                    if idx >= 0 and comp_idx > idx:
                        result.errors.append(
                            f"Variable {var_name}: N_COMPONENT must be leftmost of spatiotemporal dimensions"
                        )
                        break

            # Check T, Z, Y, X ordering
            indices = [(t_idx, "TIME"), (z_idx, "Z"), (y_idx, "Y"), (x_idx, "X")]
            indices = [(i, name) for i, name in indices if i >= 0]

            if len(indices) > 1:
                for i in range(len(indices) - 1):
                    if indices[i][0] > indices[i + 1][0]:
                        result.warnings.append(
                            f"Variable {var_name}: Dimensions not in T,Z,Y,X order"
                        )
                        break

    def _validate_variables(
        self, ds: xr.Dataset, file_type: str, result: ValidationResult
    ) -> None:
        """Validate variables and their attributes."""
        # Check coordinate variables (generic)
        self._validate_coordinates(ds, result)

        # Check array-specific required variables
        self._validate_array_specific_variables(ds, file_type, result)

        # Validate variable attributes (generic)
        for var_name, var in ds.variables.items():
            self._validate_variable_attributes(var_name, var, result)

    def _validate_array_specific_variables(
        self, ds: xr.Dataset, file_type: str, result: ValidationResult
    ) -> None:
        """Validate array-specific variable requirements."""
        if file_type not in self.array_specs["file_requirements"]:
            return

        requirements = self.array_specs["file_requirements"][file_type]

        # Check required variables
        if "required_variables" in requirements:
            for var_name in requirements["required_variables"]:
                if var_name not in ds.data_vars:
                    result.errors.append(
                        f"Required variable {var_name} missing for {file_type}"
                    )

    def _validate_coordinates(self, ds: xr.Dataset, result: ValidationResult) -> None:
        """Validate coordinate variables using generic specifications."""
        for coord_name, coord_spec in self.generic_specs["coordinate_specs"].items():
            if coord_name in ds.coords:
                coord_var = ds[coord_name]

                # Check axis attribute
                if "axis" in coord_spec:
                    expected_axis = coord_spec["axis"]
                    if (
                        "axis" not in coord_var.attrs
                        or coord_var.attrs["axis"] != expected_axis
                    ):
                        result.errors.append(
                            f"{coord_name} coordinate must have axis='{expected_axis}'"
                        )

                # Check units attribute
                if "units" in coord_spec:
                    expected_units = coord_spec["units"]
                    if "units" not in coord_var.attrs:
                        result.errors.append(
                            f"{coord_name} coordinate must have units attribute"
                        )
                    elif coord_var.attrs["units"] != expected_units:
                        result.errors.append(
                            f"{coord_name} units must be '{expected_units}', got '{coord_var.attrs['units']}'"
                        )
                elif coord_name == "TIME":
                    # For datetime coordinates, xarray handles units encoding automatically
                    # Check if it's a datetime coordinate first
                    if coord_var.dtype.kind == "M":  # numpy datetime64 type
                        # xarray handles datetime encoding, units are in the encoding, not attrs
                        pass  # This is fine, xarray manages datetime units automatically
                    elif "units" not in coord_var.attrs:
                        # Only require units attribute for non-datetime TIME coordinates
                        result.errors.append(
                            f"{coord_name} coordinate must have units attribute"
                        )

            elif coord_spec.get("required", False):
                result.errors.append(f"{coord_name} coordinate is required")

    def _validate_variable_attributes(
        self, var_name: str, var: xr.DataArray, result: ValidationResult
    ) -> None:
        """Validate individual variable attributes."""
        # Required attributes for all variables
        required_attrs = ["long_name", "units"]

        # Variables that don't need physical units (descriptive/categorical variables)
        unitless_variables = ["TRANSPORT_NAME", "TRANSPORT_DESCRIPTION"]

        for attr in required_attrs:
            if attr not in var.attrs:
                # Special handling for datetime coordinates - xarray manages units automatically
                if attr == "units" and var.dtype.kind == "M":  # datetime64 type
                    continue  # Skip units requirement for datetime variables
                # Special handling for descriptive variables that don't have physical units
                if attr == "units" and var_name in unitless_variables:
                    continue  # Skip units requirement for descriptive/categorical variables
                result.errors.append(
                    f"Variable {var_name} missing required attribute: {attr}"
                )

        # Check _FillValue data type
        if "_FillValue" in var.attrs:
            fill_value = var.attrs["_FillValue"]
            if not isinstance(fill_value, type(var.values.flat[0])):
                result.warnings.append(
                    f"Variable {var_name}: _FillValue type doesn't match variable dtype"
                )

        # Check vocabulary if present
        if "vocabulary" in var.attrs:
            vocab_url = var.attrs["vocabulary"]
            standard_name = var.attrs.get("standard_name", "")

            required_vocabs = self.generic_specs["required_vocabularies"]
            if standard_name in required_vocabs:
                expected_vocab = required_vocabs[standard_name]
                if vocab_url != expected_vocab:
                    result.errors.append(
                        f"Variable {var_name}: Wrong vocabulary URL. Expected {expected_vocab}, got {vocab_url}"
                    )

        # Check units against approved list using standard_name
        if "units" in var.attrs:
            units = var.attrs["units"]
            standard_name = var.attrs.get("standard_name", "")

            # Special cases for coordinate variables (may not have standard_name)
            if var_name == "TIME" and standard_name == "":
                approved_units = self.generic_specs["approved_units_by_standard_name"]
                if units != approved_units["time"]:
                    result.errors.append(
                        f"Variable {var_name}: Non-compliant time units '{units}', expected '{approved_units['time']}'"
                    )
            elif var_name in ["LATITUDE", "LONGITUDE", "DEPTH"] and standard_name == "":
                approved_units = self.generic_specs["approved_units_by_standard_name"]
                coord_key = var_name.lower()
                if coord_key in approved_units and units != approved_units[coord_key]:
                    result.errors.append(
                        f"Variable {var_name}: Non-compliant {coord_key} units '{units}', expected '{approved_units[coord_key]}'"
                    )

            # For variables with standard_name, validate units based on standard_name
            elif standard_name:
                approved_units = self.generic_specs["approved_units_by_standard_name"]
                alternative_units = self.generic_specs.get("alternative_units", {})

                if standard_name in approved_units:
                    expected_units = approved_units[standard_name]
                    acceptable_units = [expected_units]

                    # Add alternative units if available
                    if standard_name in alternative_units:
                        acceptable_units.extend(alternative_units[standard_name])

                    if units not in acceptable_units:
                        if len(acceptable_units) == 1:
                            result.errors.append(
                                f"Variable {var_name} (standard_name='{standard_name}'): Non-compliant units '{units}', expected '{expected_units}'"
                            )
                        else:
                            result.errors.append(
                                f"Variable {var_name} (standard_name='{standard_name}'): Non-compliant units '{units}', expected one of {acceptable_units}"
                            )

                # If standard_name not in our approved list, just issue a warning
                elif standard_name not in approved_units:
                    result.warnings.append(
                        f"Variable {var_name}: Unknown standard_name '{standard_name}' - cannot validate units '{units}'"
                    )

    def _validate_global_attributes(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate global attributes (generic and array-specific)."""
        # Generic global attribute checks
        self._validate_generic_global_attributes(ds, result)

        # Array-specific global attribute checks
        self._validate_array_specific_global_attributes(ds, result)

        # Additional validations
        self._validate_additional_global_attributes(ds, result)

    def _validate_generic_global_attributes(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate generic global attributes required for all AC1 files."""
        # Check required attributes
        for attr in self.generic_specs["required_global_attrs"]:
            if attr not in ds.attrs:
                result.errors.append(f"Missing required global attribute: {attr}")

        # Check conventions
        if "Conventions" in ds.attrs:
            conventions = ds.attrs["Conventions"]
            for conv in self.generic_specs["required_conventions"]:
                if conv not in conventions:
                    result.errors.append(f"Conventions must include '{conv}'")

    def _validate_array_specific_global_attributes(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate array-specific global attributes."""
        # Check array-specific values
        if (
            "site_code" in ds.attrs
            and ds.attrs["site_code"] != self.array_specs["site_code"]
        ):
            result.errors.append(
                f"site_code must be '{self.array_specs['site_code']}' for {self.array_specs['site_code']} data"
            )

        if "array" in ds.attrs and ds.attrs["array"] != self.array_specs["array"]:
            result.errors.append(
                f"array must be '{self.array_specs['array']}' for {self.array_specs['array']} data"
            )

        if (
            "data_mode" in ds.attrs
            and ds.attrs["data_mode"] != self.array_specs["data_mode"]
        ):
            result.errors.append(
                f"data_mode must be '{self.array_specs['data_mode']}' for {self.array_specs['site_code']} data"
            )

    def _validate_additional_global_attributes(
        self, ds: xr.Dataset, result: ValidationResult
    ) -> None:
        """Validate additional global attribute requirements."""
        # Check time format deviation
        for time_attr in ["time_coverage_start", "time_coverage_end"]:
            if time_attr in ds.attrs:
                time_str = ds.attrs[time_attr]
                if not re.match(r"\d{8}T\d{6}$", time_str):
                    result.errors.append(f"{time_attr} must use format YYYYmmddTHHMMss")

        # Check contributor role vocabulary (warning for non-standard, error for invalid URL)
        if "contributor_role_vocabulary" in ds.attrs:
            vocab_url = ds.attrs["contributor_role_vocabulary"]
            expected_url = "https://vocab.nerc.ac.uk/collection/G04/current/"

            # Check if it's a valid URL format
            if not (vocab_url.startswith(("http://", "https://"))):
                result.errors.append(
                    f"contributor_role_vocabulary must be a valid URL, got '{vocab_url}'"
                )
            elif vocab_url != expected_url:
                result.warnings.append(
                    f"contributor_role_vocabulary is non-standard. Expected '{expected_url}', got '{vocab_url}'"
                )

        # Check contributor_id format (flexible for different ID types)
        if "contributor_id" in ds.attrs:
            id_str = ds.attrs["contributor_id"]
            ids = [id_val.strip() for id_val in id_str.split(",")]
            for id_val in ids:
                # If it claims to be ORCID, validate the format
                if "orcid.org" in id_val.lower():
                    if not re.match(
                        r"https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", id_val
                    ):
                        result.errors.append(
                            f"Invalid ORCID format: {id_val}. Must be https://orcid.org/XXXX-XXXX-XXXX-XXXX"
                        )
                # For other ID types, just check it's not empty and contains some structure
                elif not id_val or len(id_val.strip()) < 3:
                    result.errors.append(
                        f"contributor_id entries must be meaningful identifiers, got: '{id_val}'"
                    )

        # Validate new mandatory OceanSITES attributes
        # Check data_mode values
        if "data_mode" in ds.attrs:
            valid_data_modes = ["R", "P", "D"]  # Real-time, Provisional, Delayed
            if ds.attrs["data_mode"] not in valid_data_modes:
                result.errors.append(
                    f"data_mode must be one of {valid_data_modes}, got '{ds.attrs['data_mode']}'"
                )

        # Check QC_indicator values
        if "QC_indicator" in ds.attrs:
            valid_qc_indicators = ["unknown", "excellent", "probably good", "mixed"]
            if ds.attrs["QC_indicator"] not in valid_qc_indicators:
                result.errors.append(
                    f"QC_indicator must be one of {valid_qc_indicators}, got '{ds.attrs['QC_indicator']}'"
                )

        # Check cdm_data_type values
        if "cdm_data_type" in ds.attrs:
            valid_cdm_types = [
                "TimeSeries",
                "TimeSeriesProfile",
                "Trajectory",
                "TrajectoryProfile",
                "Profile",
            ]
            if ds.attrs["cdm_data_type"] not in valid_cdm_types:
                result.errors.append(
                    f"cdm_data_type must be one of {valid_cdm_types}, got '{ds.attrs['cdm_data_type']}'"
                )

        # Check date_created format (use same compact format as time_coverage)
        if "date_created" in ds.attrs:
            date_str = ds.attrs["date_created"]
            if not re.match(r"\d{8}T\d{6}$", date_str):
                result.errors.append(
                    f"date_created must use format YYYYmmddTHHMMss, got '{date_str}'"
                )

        # Check id format (should match filename pattern)
        if "id" in ds.attrs:
            id_str = ds.attrs["id"]
            if not re.match(
                r"^OS_[A-Z0-9]+_\d{8}-\d{8}_[A-Z]{3}_[A-Za-z0-9_T]+$", id_str
            ):
                result.warnings.append(
                    f"id should follow OceanSITES pattern OS_ARRAY_YYYYMMDD-YYYYMMDD_TYPE_CONTENT, got '{id_str}'"
                )

    def _validate_data_values(
        self, ds: xr.Dataset, filepath: str, result: ValidationResult
    ) -> None:
        """Validate actual data values."""
        # Extract date range from filename
        filename = Path(filepath).name
        general_match = re.match(
            self.generic_specs["general_filename_pattern"], filename
        )
        if not general_match:
            return  # Skip if can't parse filename

        start_date = datetime.strptime(general_match.group(2), "%Y%m%d")
        end_date = datetime.strptime(general_match.group(3), "%Y%m%d")

        # Validate coordinate values using generic specs
        for coord_name, coord_spec in self.generic_specs["coordinate_specs"].items():
            if coord_name in ds.coords:
                coord_vals = ds[coord_name].values

                # Check value ranges
                if "range" in coord_spec:
                    min_val, max_val = coord_spec["range"]
                    if np.any((coord_vals < min_val) | (coord_vals > max_val)):
                        result.errors.append(
                            f"{coord_name} values must be between {min_val} and {max_val}"
                        )

                # Check depth positive direction
                elif coord_name == "DEPTH" and "positive_down_range" in coord_spec:
                    depth_var = ds[coord_name]
                    positive = depth_var.attrs.get("positive", "down")

                    if positive == "down":
                        min_val, max_val = coord_spec["positive_down_range"]
                        if np.any(coord_vals < min_val):
                            result.errors.append(
                                f"DEPTH values must be ≥{min_val} when positive='down'"
                            )
                    elif positive == "up" and np.any(coord_vals > 0):
                        result.errors.append(
                            "DEPTH values must be ≤0 when positive='up'"
                        )

        # Validate TIME values against filename date range
        if "TIME" in ds.coords:
            time_var = ds["TIME"]
            if "units" in time_var.attrs:
                try:
                    # Convert to datetime
                    time_values = xr.decode_cf(ds)["TIME"].values
                    file_start = np.datetime64(start_date)
                    file_end = np.datetime64(
                        end_date + timedelta(days=1)
                    )  # End of end date

                    if np.any(time_values < file_start) or np.any(
                        time_values >= file_end
                    ):
                        result.errors.append(
                            "TIME values must fall within filename date range"
                        )
                except (ValueError, TypeError, AttributeError):
                    result.warnings.append(
                        "Could not validate TIME values against filename dates"
                    )

        # Check valid_min/valid_max for variables that specify them
        for var_name, var in ds.data_vars.items():
            if "valid_min" in var.attrs and "valid_max" in var.attrs:
                valid_min = var.attrs["valid_min"]
                valid_max = var.attrs["valid_max"]

                # Only check non-NaN values
                valid_data = var.values[~np.isnan(var.values)]
                if len(valid_data) > 0:
                    if np.any(valid_data < valid_min) or np.any(valid_data > valid_max):
                        result.warnings.append(
                            f"Variable {var_name} has values outside valid range [{valid_min}, {valid_max}]"
                        )


def validate_ac1_file(filepath: str, array_specs: dict = None) -> ValidationResult:
    """Convenience function to validate an AC1 file.

    Parameters
    ----------
    filepath : str
        Path to the NetCDF file to validate
    array_specs : dict, optional
        Array-specific specifications. Defaults to RAPID_SPECS.

    Returns
    -------
    ValidationResult
        Validation results

    """
    checker = AC1ComplianceChecker(array_specs)
    return checker.validate_file(filepath)


def print_validation_report(result: ValidationResult, filepath: str) -> None:
    """Print a formatted validation report.

    Parameters
    ----------
    result : ValidationResult
        Validation results
    filepath : str
        Path to the validated file

    """
    print(f"\n{'=' * 60}")
    print(f"AC1 Compliance Report: {Path(filepath).name}")
    print(f"{'=' * 60}")

    if result.file_type:
        print(f"File Type: {result.file_type}")

    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")

    if result.errors:
        print(f"\n{'-' * 30} ERRORS {'-' * 30}")
        for i, error in enumerate(result.errors, 1):
            print(f"{i:2d}. {error}")

    if result.warnings:
        print(f"\n{'-' * 29} WARNINGS {'-' * 29}")
        for i, warning in enumerate(result.warnings, 1):
            print(f"{i:2d}. {warning}")

    print(f"\n{'=' * 60}")


def create_array_specs_template() -> dict:
    """Create a template for array-specific specifications.

    Returns
    -------
    dict
        Template dictionary showing required structure for array specs

    """
    return {
        "file_patterns": {
            "file_type_1": r"^OS_ARRAY_(\d{8})-(\d{8})_DPR_content_TRES\.nc$",
            # Add more file types as needed
        },
        "site_code": "ARRAY_NAME",
        "array": "ARRAY_NAME",
        "data_mode": "D",  # or 'R' for real-time
        "file_requirements": {
            "file_type_1": {
                "dimensions": {"DIM_NAME": 123},  # Required dimensions with sizes
                "forbidden_dimensions": [
                    "FORBIDDEN_DIM"
                ],  # Dimensions that should not exist
                "required_variables": ["VAR1", "VAR2"],  # Required data variables
            }
        },
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python compliance_checker.py <filepath>")
        print("\nThis will validate using RAPID array specifications.")
        print(
            "To use different array specs, call validate_ac1_file() directly with array_specs parameter."
        )
        sys.exit(1)

    filepath = sys.argv[1]
    result = validate_ac1_file(filepath)
    print_validation_report(result, filepath)

    sys.exit(0 if result.passed else 1)
