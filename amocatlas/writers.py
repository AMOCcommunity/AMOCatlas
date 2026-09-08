"""Data writing utilities for AMOCatlas.

This module provides functions for writing and exporting AMOCatlas datasets
to various formats, with special handling for NetCDF export, attribute
sanitization, and datetime encoding. Includes functions to save datasets
with proper compression and metadata formatting.
"""

import json
from numbers import Number

import numpy as np
import xarray as xr

from amocatlas import logger


def save_dataset(ds: xr.Dataset, output_file: str = "../test.nc") -> bool:
    """Attempts to save the dataset to a NetCDF file. If a TypeError occurs due to invalid attribute values,
    it converts the invalid attributes to strings and retries the save operation.

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset to be saved.
    output_file : str, optional
        The path to the output NetCDF file. Defaults to '../test.nc'.

    Returns
    -------
    bool
        True if the dataset was saved successfully, False otherwise.

    Notes
    -----
    This function is based on a workaround for issues with saving datasets containing
    attributes of unsupported types. See: https://github.com/pydata/xarray/issues/3743

    """
    valid_types: tuple[type | tuple, ...] = (
        str,
        int,
        float,
        np.float32,
        np.float64,
        np.int32,
        np.int64,
    )
    # More general
    valid_types = (str, Number, np.ndarray, np.number, list, tuple)

    # Make a copy to avoid modifying the original dataset
    ds_copy = ds.copy()

    # Sanitize attributes for netCDF serialization. NETCDF4_CLASSIC does not support
    # NC_STRING attributes, so values that would serialise as one are converted to a single
    # string up front: None -> ""; dicts (e.g. applied_variable_mapping) and lists/tuples
    # that contain strings (e.g. variables_to_remove) are JSON-encoded. Numeric lists are
    # left as-is (they write as a valid numeric array attribute).
    def _sanitize_attr(value: object) -> object:
        if value is None:
            return ""
        if isinstance(value, dict):
            return json.dumps(value)
        if isinstance(value, (list, tuple)) and (
            not value
            or not all(isinstance(x, Number) and not isinstance(x, bool) for x in value)
        ):
            return json.dumps(list(value))
        return value

    new_attrs = {k: _sanitize_attr(v) for k, v in ds_copy.attrs.items()}
    ds_copy.attrs.clear()
    ds_copy.attrs.update(new_attrs)

    # Same sanitisation for variable-level attributes.
    for var_name in ds_copy.variables:
        var_attrs = ds_copy[var_name].attrs
        for key in list(var_attrs):
            var_attrs[key] = _sanitize_attr(var_attrs[key])

    # Handle datetime coordinate encoding conflicts
    # For datetime variables, remove manual units to let xarray handle encoding properly
    conflicting_keys = ["units", "calendar"]
    for var_name, variable in ds_copy.variables.items():
        if np.issubdtype(variable.dtype, np.datetime64):
            logger.log_info(
                f"Configuring datetime encoding for variable '{var_name}' - removing manual units"
            )

            # Remove conflicting attributes that may clash with encoding
            for key in conflicting_keys:
                if key in ds_copy[var_name].attrs:
                    del ds_copy[var_name].attrs[key]

            # Pin the datetime encoding on the VARIABLE (ds_copy[var].encoding), not the
            # dataset-level ds_copy.encoding[var] — the latter is ignored on write, which
            # let each array keep its source units (e.g. "days since 2004-4-1"). Set a
            # fresh dict so stale source keys (old units/dtype/_FillValue) can't conflict;
            # float64 avoids the int32 "seconds since 1970" overflow (Y2038) for modern dates.
            ds_copy[var_name].encoding = {
                "units": "seconds since 1970-01-01T00:00:00Z",
                "calendar": "gregorian",
                "dtype": "float64",
            }

    # Set up compression encoding for data variables
    encoding = {}
    for var in ds_copy.data_vars:
        encoding[var] = {"zlib": True, "complevel": 4}

    try:
        ds_copy.to_netcdf(output_file, format="NETCDF4_CLASSIC", encoding=encoding)
    except TypeError as e:
        print(e.__class__.__name__, e)

        # Convert invalid global dataset attributes to strings
        for k, v in ds_copy.attrs.items():
            if not isinstance(v, valid_types) or isinstance(v, bool):
                print(
                    f"global: Converting attribute '{k}' with value '{v}' to string.",
                )
                ds_copy.attrs[k] = str(v)

        # Convert invalid variable attributes to strings
        for varname, variable in ds_copy.variables.items():
            for k, v in variable.attrs.items():
                if not isinstance(v, valid_types) or isinstance(v, bool):
                    print(
                        f"variable '{varname}': Converting attribute '{k}' with value '{v}' to string.",
                    )
                    variable.attrs[k] = str(v)
        try:
            ds_copy.to_netcdf(output_file, format="NETCDF4_CLASSIC", encoding=encoding)
        except (OSError, ValueError, RuntimeError) as e:
            print("Failed to save dataset:", e)
            datetime_vars = [
                var
                for var in ds_copy.variables
                if ds_copy[var].dtype == "datetime64[ns]"
            ]
            print("Variables with dtype datetime64[ns]:", datetime_vars)
            float_attrs = [
                attr for attr in ds_copy.attrs if isinstance(ds_copy.attrs[attr], float)
            ]
            print("Attributes with dtype float64:", float_attrs)
            return False
        else:
            return True
    else:
        return True
