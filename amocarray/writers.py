from numbers import Number
from typing import Union, Any, Dict

import numpy as np
import xarray as xr
import yaml
from pathlib import Path

from amocarray import logger

log = logger.log  # Use the global logger


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
    valid_types: tuple[Union[type, tuple], ...] = (
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
    try:
        ds.to_netcdf(output_file, format="NETCDF4_CLASSIC")
        return True
    except TypeError as e:
        print(e.__class__.__name__, e)
        for varname, variable in ds.variables.items():
            for k, v in variable.attrs.items():
                if not isinstance(v, valid_types) or isinstance(v, bool):
                    print(
                        f"variable '{varname}': Converting attribute '{k}' with value '{v}' to string.",
                    )
                    variable.attrs[k] = str(v)
        try:
            ds.to_netcdf(output_file, format="NETCDF4_CLASSIC")
            return True
        except Exception as e:
            print("Failed to save dataset:", e)
            datetime_vars = [
                var for var in ds.variables if ds[var].dtype == "datetime64[ns]"
            ]
            print("Variables with dtype datetime64[ns]:", datetime_vars)
            float_attrs = [
                attr for attr in ds.attrs if isinstance(ds.attrs[attr], float)
            ]
            print("Attributes with dtype float64:", float_attrs)
            return False



def export_attributes_to_yaml(
        dataset: xr.Dataset,
        output_path: str | Path = None,
        file_name: str = "attributes.yaml",
        indent: int = 2,
        sort_keys: bool = False
) -> Dict[str, Any]:
    """
    Export global and variable attributes from an xarray Dataset to YAML format.

    Parameters
    ----------
    dataset : xr.Dataset
        Input xarray Dataset containing attributes
    output_path : str | Paths, default=None
        Directory path to save the YAML file. If None, returns dict without writing.
    file_name : str, default="attributes.yaml"
        Name of the output YAML file
    indent : int, default=2
        Indentation level for the YAML file
    sort_keys : bool, default=False
        Whether to sort keys alphabetically in the output

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all attributes in hierarchical structure

    Examples
    --------
    >>> ds = xr.Dataset(
    ...     {"temp": ("x", [1, 2], {"units": "K", "long_name": "Temperature"})},
    ...     attrs={"title": "Example Dataset", "version": "1.0"}
    ... )
    >>> export_attributes_to_yaml(ds, "metadata/")
    """

    attributes_dict = {
        "global_attributes": dict(dataset.attrs),
        "variables": {}
    }


    for var_name in dataset.variables:
        var = dataset[var_name]
        attributes_dict["variables"][var_name] = dict(var.attrs)

    # Write to YAML file if output path is specified
    if output_path is not None:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / file_name

        with open(output_file, 'w') as f:
            yaml.dump(
                attributes_dict,
                stream=f,
                indent=indent,
                sort_keys=sort_keys,
                default_flow_style=False,
                allow_unicode=True
            )

    return attributes_dict

