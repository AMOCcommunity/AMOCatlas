import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from pandas import DataFrame
from pandas.io.formats.style import Styler


# ------------------------------------------------------------------------------------
# Views of the ds or nc file
# ------------------------------------------------------------------------------------
def show_contents(
    data: str | xr.Dataset,
    content_type: str = "variables",
) -> Styler | pd.DataFrame:
    """Wrapper function to show contents of an xarray Dataset or a netCDF file.

    Parameters
    ----------
    data : str or xr.Dataset
        The input data, either a file path to a netCDF file or an xarray Dataset.
    content_type : str, optional
        The type of content to show, either 'variables' (or 'vars') or 'attributes' (or 'attrs').
        Default is 'variables'.

    Returns
    -------
    pandas.io.formats.style.Styler or pandas.DataFrame
        A styled DataFrame with details about the variables or attributes.

    Raises
    ------
    TypeError
        If the input data is not a file path (str) or an xarray Dataset.
    ValueError
        If the content_type is not 'variables' (or 'vars') or 'attributes' (or 'attrs').

    """
    if content_type in ["variables", "vars"]:
        if isinstance(data, (str, xr.Dataset)):
            return show_variables(data)
        else:
            raise TypeError("Input data must be a file path (str) or an xarray Dataset")
    elif content_type in ["attributes", "attrs"]:
        if isinstance(data, (str, xr.Dataset)):
            return show_attributes(data)
        else:
            raise TypeError(
                "Attributes can only be shown for netCDF files (str) or xarray Datasets",
            )
    else:
        raise ValueError(
            "content_type must be either 'variables' (or 'vars') or 'attributes' (or 'attrs')",
        )


def show_variables(data: str | xr.Dataset) -> Styler:
    """Processes an xarray Dataset or a netCDF file, extracts variable information,
    and returns a styled DataFrame with details about the variables.

    Parameters
    ----------
    data : str or xr.Dataset
        The input data, either a file path to a netCDF file or an xarray Dataset.

    Returns
    -------
    pd.io.formats.style.Styler
        A styled DataFrame containing the following columns:
        - dims: The dimension of the variable (or "string" if it is a string type).
        - name: The name of the variable.
        - units: The units of the variable (if available).
        - comment: Any additional comments about the variable (if available).
        - standard_name: The standard name of the variable (if available).
        - dtype: The data type of the variable.

    Raises
    ------
    TypeError
        If the input data is not a file path (str) or an xarray Dataset.

    """
    from netCDF4 import Dataset
    from pandas import DataFrame

    if isinstance(data, str):
        print(f"information is based on file: {data}")
        dataset = Dataset(data)
        variables = dataset.variables
    elif isinstance(data, xr.Dataset):
        print("information is based on xarray Dataset")
        variables = data.variables
    else:
        raise TypeError("Input data must be a file path (str) or an xarray Dataset")

    info = {}
    for i, key in enumerate(variables):
        var = variables[key]
        if isinstance(data, str):
            dims = var.dimensions[0] if len(var.dimensions) == 1 else "string"
            units = "" if not hasattr(var, "units") else var.units
            comment = "" if not hasattr(var, "comment") else var.comment
        else:
            dims = var.dims[0] if len(var.dims) == 1 else "string"
            units = var.attrs.get("units", "")
            comment = var.attrs.get("comment", "")

        info[i] = {
            "name": key,
            "dims": dims,
            "units": units,
            "comment": comment,
            "standard_name": var.attrs.get("standard_name", ""),
            "dtype": str(var.dtype) if isinstance(data, str) else str(var.data.dtype),
        }

    vars = DataFrame(info).T

    dim = vars.dims
    dim[dim.str.startswith("str")] = "string"
    vars["dims"] = dim

    vars = (
        vars.sort_values(["dims", "name"])
        .reset_index(drop=True)
        .loc[:, ["dims", "name", "units", "comment", "standard_name", "dtype"]]
        .set_index("name")
        .style
    )

    return vars


def show_attributes(data: str | xr.Dataset) -> pd.DataFrame:
    """Processes an xarray Dataset or a netCDF file, extracts attribute information,
    and returns a DataFrame with details about the attributes.

    Parameters
    ----------
    data : str or xr.Dataset
        The input data, either a file path to a netCDF file or an xarray Dataset.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the following columns:
        - Attribute: The name of the attribute.
        - Value: The value of the attribute.
        - DType: The data type of the attribute.

    Raises
    ------
    TypeError
        If the input data is not a file path (str) or an xarray Dataset.

    """
    from netCDF4 import Dataset
    from pandas import DataFrame

    if isinstance(data, str):
        print(f"information is based on file: {data}")
        rootgrp = Dataset(data, "r", format="NETCDF4")
        attributes = rootgrp.ncattrs()
        get_attr = lambda key: getattr(rootgrp, key)
    elif isinstance(data, xr.Dataset):
        print("information is based on xarray Dataset")
        attributes = data.attrs.keys()
        get_attr = lambda key: data.attrs[key]
    else:
        raise TypeError("Input data must be a file path (str) or an xarray Dataset")

    info = {}
    for i, key in enumerate(attributes):
        dtype = type(get_attr(key)).__name__
        info[i] = {"Attribute": key, "Value": get_attr(key), "DType": dtype}

    attrs = DataFrame(info).T

    return attrs


def show_variables_by_dimension(
    data: str | xr.Dataset,
    dimension_name: str = "trajectory",
) -> Styler:
    """Extracts variable information from an xarray Dataset or a netCDF file and returns a styled DataFrame
    with details about the variables filtered by a specific dimension.

    Parameters
    ----------
    data : str or xr.Dataset
        The input data, either a file path to a netCDF file or an xarray Dataset.
    dimension_name : str, optional
        The name of the dimension to filter variables by, by default "trajectory".

    Returns
    -------
    pandas.io.formats.style.Styler
        A styled DataFrame containing the following columns:
        - dims: The dimension of the variable (or "string" if it is a string type).
        - name: The name of the variable.
        - units: The units of the variable (if available).
        - comment: Any additional comments about the variable (if available).

    Raises
    ------
    TypeError
        If the input data is not a file path (str) or an xarray Dataset.

    """
    if isinstance(data, str):
        print(f"information is based on file: {data}")
        dataset = xr.open_dataset(data)
        variables = dataset.variables
    elif isinstance(data, xr.Dataset):
        print("information is based on xarray Dataset")
        variables = data.variables
    else:
        raise TypeError("Input data must be a file path (str) or an xarray Dataset")

    info = {}
    for i, key in enumerate(variables):
        var = variables[key]
        if isinstance(data, str):
            dims = var.dimensions[0] if len(var.dimensions) == 1 else "string"
            units = "" if not hasattr(var, "units") else var.units
            comment = "" if not hasattr(var, "comment") else var.comment
        else:
            dims = var.dims[0] if len(var.dims) == 1 else "string"
            units = var.attrs.get("units", "")
            comment = var.attrs.get("comment", "")

        if dims == dimension_name:
            info[i] = {
                "name": key,
                "dims": dims,
                "units": units,
                "comment": comment,
            }

    vars = DataFrame(info).T

    dim = vars.dims
    dim[dim.str.startswith("str")] = "string"
    vars["dims"] = dim

    vars = (
        vars.sort_values(["dims", "name"])
        .reset_index(drop=True)
        .loc[:, ["dims", "name", "units", "comment"]]
        .set_index("name")
        .style
    )

    return vars


def monthly_resample(da: xr.DataArray) -> xr.DataArray:
    """Resample to monthly mean if data is not already monthly."""
    time_key = [c for c in da.coords if c.lower() == "time"]
    if not time_key:
        raise ValueError("No time coordinate found.")
    time_key = time_key[0]

    # Extract time values and check spacing
    time_values = da[time_key].values
    dt_days = np.nanmean(np.diff(time_values) / np.timedelta64(1, "D"))
    if 20 <= dt_days <= 40:
        return da  # Already monthly

    # Drop NaT timestamps
    mask_valid_time = ~np.isnat(time_values)
    da = da.isel({time_key: mask_valid_time})

    # Drop duplicate timestamps (keep first)
    _, unique_indices = np.unique(da[time_key].values, return_index=True)
    da = da.isel({time_key: np.sort(unique_indices)})

    # Ensure strictly increasing time
    da = da.sortby(time_key)

    # Now resample
    return da.resample({time_key: "1MS"}).mean()


def plot_amoc_timeseries(
    data,
    varnames=None,
    labels=None,
    colors=None,
    title="AMOC Time Series",
    ylabel=None,
    time_limits=None,
    ylim=None,
    figsize=(10, 3),
    resample_monthly=True,
    plot_raw=True,
):
    """
    Plot original and optionally monthly-averaged AMOC time series for one or more datasets.

    Parameters
    ----------
    data : list of xarray.Dataset or xarray.DataArray
        List of datasets or DataArrays to plot.
    varnames : list of str, optional
        List of variable names to extract from each dataset. Not needed if DataArrays are passed.
    labels : list of str, optional
        Labels for the legend.
    colors : list of str, optional
        Colors for monthly-averaged plots.
    title : str
        Title of the plot.
    ylabel : str, optional
        Label for the y-axis. If None, inferred from attributes.
    time_limits : tuple of str or pd.Timestamp, optional
        X-axis time limits (start, end).
    ylim : tuple of float, optional
        Y-axis limits (min, max).
    figsize : tuple
        Size of the figure.
    resample_monthly : bool
        If True, monthly averages are computed and plotted.
    plot_raw : bool
        If True, raw data is plotted.
    """
    if not isinstance(data, list):
        data = [data]

    if varnames is None:
        varnames = [None] * len(data)
    if labels is None:
        labels = [f"Dataset {i+1}" for i in range(len(data))]
    if colors is None:
        colors = ["red", "darkblue", "green", "purple", "orange"]

    fig, ax = plt.subplots(figsize=figsize)

    for i, item in enumerate(data):
        label = labels[i]
        color = colors[i % len(colors)]
        var = varnames[i]

        # Extract DataArray
        if isinstance(item, xr.Dataset):
            da = item[var]
        else:
            da = item

        # Get time coordinate (case sensitive)
        for coord in da.coords:
            if coord.lower() == "time":
                time_key = coord
                break
        else:
            raise ValueError("No time coordinate found in dataset.")

        # Plot original
        if plot_raw:
            ax.plot(
                da[time_key],
                da,
                color="grey",
                alpha=0.5,
                linewidth=0.5,
                label=f"{label} (raw)" if label else "Original",
            )

        # Plot monthly average if requested
        if resample_monthly:

            da_monthly = monthly_resample(da)

            ax.plot(
                da_monthly[time_key],
                da_monthly,
                color=color,
                linewidth=1.5,
                label=f"{label} Monthly Avg",
            )

        # Attempt to extract ylabel from metadata if not provided
        if ylabel is None and "standard_name" in da.attrs and "units" in da.attrs:
            ylabel = f"{da.attrs['standard_name']} [{da.attrs['units']}]"

    # Horizontal zero line
    ax.axhline(0, color="black", linestyle="--", linewidth=0.5)

    # Styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(ylabel if ylabel else "Transport [Sv]")
    ax.legend(loc="best")
    ax.grid(True, linestyle="--", alpha=0.5)

    # Limits
    if time_limits:
        ax.set_xlim(pd.Timestamp(time_limits[0]), pd.Timestamp(time_limits[1]))
    if ylim:
        ax.set_ylim(ylim)

    plt.tight_layout()
    return fig, ax


def plot_monthly_anomalies(**kwargs) -> tuple[plt.Figure, list[plt.Axes]]:
    """
    Plot the monthly anomalies for various datasets.
    Pass keyword arguments in the form: `label_name_data`, `label_name_label`.
    For example:
        osnap_data = standardOSNAP[0]["MOC_all"], osnap_label = "OSNAP"
        ...
    """

    color_cycle = [
        "blue",
        "red",
        "green",
        "purple",
        "orange",
        "darkblue",
        "darkred",
        "darkgreen",
    ]

    # Extract and sort data/labels by name to ensure consistent ordering
    names = ["dso", "osnap", "fortyone", "rapid", "fw2015", "move", "samba"]
    datasets = [monthly_resample(kwargs[f"{name}_data"]) for name in names]
    labels = [kwargs[f"{name}_label"] for name in names]

    fig, axes = plt.subplots(len(datasets), 1, figsize=(10, 16), sharex=True)

    for i, (data, label, color) in enumerate(zip(datasets, labels, color_cycle)):
        time = data["TIME"]
        axes[i].plot(time, data, color=color, label=label)
        axes[i].axhline(0, color="black", linestyle="--", linewidth=0.5)
        axes[i].set_title(label)
        axes[i].set_ylabel("Transport [Sv]")
        axes[i].legend()
        axes[i].grid(True, linestyle="--", alpha=0.5)

        # Dynamic ylim
        ymin = float(data.min()) - 1
        ymax = float(data.max()) + 1
        axes[i].set_ylim([ymin, ymax])

        # Style choices
        axes[i].spines["top"].set_visible(False)
        axes[i].spines["right"].set_visible(False)
        axes[i].set_xlim([pd.Timestamp("2000-01-01"), pd.Timestamp("2023-12-31")])
        axes[i].set_clip_on(False)

    axes[-1].set_xlabel("Time")
    plt.tight_layout()
    return fig, axes
