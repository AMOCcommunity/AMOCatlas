import re

import numpy as np
import xarray as xr

from amocarray import logger
from amocarray.logger import log_info, log_debug

log = logger.log


def generate_reverse_conversions(
    forward_conversions: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Create a unit conversion dictionary with both forward and reverse conversions.

    Parameters
    ----------
    forward_conversions : dict of {str: dict of {str: float}}
        Mapping of source units to target units and conversion factors.
        Example: {"m": {"cm": 100, "km": 0.001}}

    Returns
    -------
    dict of {str: dict of {str: float}}
        Complete mapping of units including reverse conversions.
        Example: {"cm": {"m": 0.01}, "km": {"m": 1000}}

    Notes
    -----
    If a conversion factor is zero, a warning is printed, and the reverse conversion is skipped.

    """
    complete_conversions: dict[str, dict[str, float]] = {}

    for from_unit, targets in forward_conversions.items():
        complete_conversions.setdefault(from_unit, {})
        for to_unit, factor in targets.items():
            complete_conversions[from_unit][to_unit] = factor
            complete_conversions.setdefault(to_unit, {})
            if factor == 0:
                print(
                    f"Warning: zero factor in conversion from {from_unit} to {to_unit}",
                )
                continue
            complete_conversions[to_unit][from_unit] = 1 / factor

    return complete_conversions


# Various conversions from the key to units_name with the multiplicative conversion factor
base_unit_conversion = {
    "cm/s": {"m/s": 0.01},
    "cm s-1": {"m s-1": 0.01},
    "S/m": {"mS/cm": 0.1},
    "dbar": {"Pa": 10000, "kPa": 10},
    "degrees_Celsius": {"Celsius": 1},
    "m": {"cm": 100, "km": 0.001},
    "g m-3": {"kg m-3": 0.001},
    "Sverdrup": {"Sv": 1},
}

unit_conversion = generate_reverse_conversions(base_unit_conversion)

# Specify the preferred units, and it will convert if the conversion is available in unit_conversion
preferred_units = ["m s-1", "dbar", "S m-1", "Sv"]

# String formats for units.  The key is the original, the value is the desired format
unit_str_format = {
    "m/s": "m s-1",
    "cm/s": "cm s-1",
    "S/m": "S m-1",
    "meters": "m",
    "degrees_Celsius": "Celsius",
    "g/m^3": "g m-3",
}


def reformat_units_var(
    ds: xr.Dataset,
    var_name: str,
    unit_format: dict[str, str] = unit_str_format,
) -> str:
    """Reformat the units of a variable in the dataset based on a provided mapping.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset containing variables with units to be reformatted.
    var_name : str
        The name of the variable whose units need to be reformatted.
    unit_format : dict of {str: str}, optional
        A dictionary mapping old unit strings to new formatted unit strings.
        Defaults to `unit_str_format`.

    Returns
    -------
    str
        The reformatted unit string. If the old unit is not found in `unit_format`,
        the original unit string is returned.

    """
    old_unit = ds[var_name].attrs["units"]
    new_unit = unit_format.get(old_unit, old_unit)
    return new_unit


def convert_units_var(
    var_values: np.ndarray | float,
    current_unit: str,
    new_unit: str,
    unit_conversion: dict[str, dict[str, float]] = unit_conversion,
) -> np.ndarray | float:
    """Converts variable values from one unit to another using a predefined conversion factor.

    Parameters
    ----------
    var_values : numpy.ndarray or float
        The values to be converted.
    current_unit : str
        The current unit of the variable values.
    new_unit : str
        The target unit to which the variable values should be converted.
    unit_conversion : dict of {str: dict of {str: float}}, optional
        A dictionary containing conversion factors between units. The default is `unit_conversion`.

    Returns
    -------
    numpy.ndarray or float
        The converted variable values. If no conversion factor is found, the original values are returned.

    Raises
    ------
    KeyError
        If the conversion factor for the specified units is not found in the `unit_conversion` dictionary.

    Notes
    -----
    If the conversion factor for the specified units is not available, a message is printed, and the original
    values are returned without any conversion.

    """
    try:
        conversion_factor = unit_conversion[current_unit][new_unit]
        return var_values * conversion_factor
    except KeyError:
        print(f"No conversion information found for {current_unit} to {new_unit}")
        return var_values


def find_best_dtype(var_name: str, da: xr.DataArray) -> np.dtype:
    """Determines the most suitable data type for a given variable.

    Parameters
    ----------
    var_name : str
        The name of the variable.
    da : xarray.DataArray
        The data array containing the variable's values.

    Returns
    -------
    numpy.dtype
        The optimal data type for the variable based on its name and values.

    """
    input_dtype = da.dtype.type
    if "latitude" in var_name.lower() or "longitude" in var_name.lower():
        return np.double
    if var_name[-2:].lower() == "qc":
        return np.int8
    if "time" in var_name.lower():
        return input_dtype
    if var_name[-3:] == "raw" or "int" in str(input_dtype):
        if np.nanmax(da.values) < 2**16 / 2:
            return np.int16
        elif np.nanmax(da.values) < 2**32 / 2:
            return np.int32
    if input_dtype == np.float64:
        return np.float32
    return input_dtype


def set_fill_value(new_dtype: np.dtype) -> int:
    """Calculate the fill value for a given data type.

    Parameters
    ----------
    new_dtype : numpy.dtype
        The data type for which the fill value is to be calculated.

    Returns
    -------
    int
        The calculated fill value based on the bit-width of the data type.

    """
    fill_val: int = 2 ** (int(re.findall(r"\d+", str(new_dtype))[0]) - 1) - 1
    return fill_val


def set_best_dtype(ds: xr.Dataset) -> xr.Dataset:
    """Adjust the data types of variables in a dataset to optimize memory usage.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset whose variables' data types will be adjusted.

    Returns
    -------
    xarray.Dataset
        The dataset with updated data types for its variables, potentially saving memory.

    Notes
    -----
    - The function determines the best data type for each variable using `find_best_dtype`.
    - Attributes like `valid_min` and `valid_max` are updated to match the new data type.
    - If the new data type is integer-based, NaN values are replaced with a fill value.
    - Logs the percentage of memory saved after the data type adjustments.

    """
    bytes_in: int = ds.nbytes
    for var_name in list(ds):
        da: xr.DataArray = ds[var_name]
        input_dtype: np.dtype = da.dtype.type
        new_dtype: np.dtype = find_best_dtype(var_name, da)
        for att in ["valid_min", "valid_max"]:
            if att in da.attrs.keys():
                da.attrs[att] = np.array(da.attrs[att]).astype(new_dtype)
        if new_dtype == input_dtype:
            continue
        log_debug(f"{var_name} input dtype {input_dtype} change to {new_dtype}")
        da_new: xr.DataArray = da.astype(new_dtype)
        ds = ds.drop_vars(var_name)
        if "int" in str(new_dtype):
            fill_val: int = set_fill_value(new_dtype)
            da_new[np.isnan(da)] = fill_val
            da_new.encoding["_FillValue"] = fill_val
        ds[var_name] = da_new
    bytes_out: int = ds.nbytes
    log_info(
        f"Space saved by dtype downgrade: {int(100 * (bytes_in - bytes_out) / bytes_in)} %",
    )
    return ds
