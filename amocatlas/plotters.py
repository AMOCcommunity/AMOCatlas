"""AMOCatlas plotting functions for visualization and publication figures."""

import contextlib
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from pandas import DataFrame
from pandas.io.formats.style import Styler


def _vlabel(label: str, width: int = 24) -> str:
    """Word-wrap a long variable label for a plot axis.

    Standardised ``long_name`` values (e.g. "meridional overturning transport anomaly,
    western-boundary bottom-pressure contribution") overflow a y-axis. This breaks the label
    onto multiple lines at word boundaries so it fits, without splitting words. Short labels
    are returned unchanged.

    A future version may translate names via a label registry (cf. ``oceanarray``'s
    ``vlabel``); for now it only wraps.

    Parameters
    ----------
    label : str
        The axis label text.
    width : int, optional
        Target maximum characters per line (default 24).

    Returns
    -------
    str
        The label with newlines inserted, or the original if it is short or empty.

    """
    if not label or len(label) <= width:
        return label
    wrapped = textwrap.wrap(label, width=width, break_long_words=False)
    return "\n".join(wrapped) if wrapped else label


def format_variable_name_for_plotting(name: str) -> str:
    r"""Convert variable names with subscripts to matplotlib LaTeX format.

    This function translates variable naming patterns that include Greek letters
    and other subscripts into proper matplotlib LaTeX syntax for publication-quality plots.

    Parameters
    ----------
    name : str
        Variable name that may contain subscript patterns.

    Returns
    -------
    str
        Variable name formatted with matplotlib LaTeX syntax for subscripts.

    Examples
    --------
    >>> format_variable_name_for_plotting("MOC_sigma0")
    'MOC$_{\\sigma_0}$'
    >>> format_variable_name_for_plotting("MOC_z")
    'MOC$_{z}$'
    >>> format_variable_name_for_plotting("density_theta")
    'density$_{\\theta}$'
    >>> format_variable_name_for_plotting("temp_ref")
    'temp$_{ref}$'

    Notes
    -----
    The function converts patterns with underscores to LaTeX subscripts:
    - Single letters: MOC_z → MOC$_{z}$
    - Greek patterns: MOC_sigma → MOC$_{\\sigma}$
    - Numbers: MOC_sigma0 → MOC$_{\\sigma_0}$
    - Multiple parts: Only the first underscore pattern is converted

    Matplotlib subscript syntax: $_{text}$

    """
    # Dictionary of Greek letter patterns to LaTeX equivalents
    greek_letters = {
        "alpha": r"\alpha",
        "beta": r"\beta",
        "gamma": r"\gamma",
        "delta": r"\delta",
        "epsilon": r"\epsilon",
        "zeta": r"\zeta",
        "eta": r"\eta",
        "theta": r"\theta",
        "iota": r"\iota",
        "kappa": r"\kappa",
        "lambda": r"\lambda",
        "mu": r"\mu",
        "nu": r"\nu",
        "xi": r"\xi",
        "pi": r"\pi",
        "rho": r"\rho",
        "sigma": r"\sigma",
        "tau": r"\tau",
        "upsilon": r"\upsilon",
        "phi": r"\phi",
        "chi": r"\chi",
        "psi": r"\psi",
        "omega": r"\omega",
    }

    # Split on underscores
    parts = name.split("_")

    # If no underscores, return as is
    if len(parts) < 2:
        return name

    # Take the first part as the main variable name
    main_name = parts[0]
    subscript_part = parts[1]

    # Check if the subscript part is a Greek letter pattern
    subscript_lower = subscript_part.lower()

    # Handle special cases like "sigma0", "sigma1", etc.
    if subscript_lower.startswith("sigma") and len(subscript_lower) > 5:
        # Extract number or additional characters after sigma
        suffix = subscript_lower[5:]  # Everything after 'sigma'
        formatted_subscript = f"{greek_letters['sigma']}_{suffix}"
    elif subscript_lower in greek_letters:
        # Pure Greek letter
        formatted_subscript = greek_letters[subscript_lower]
    else:
        # Regular text subscript (including single letters like 'z')
        formatted_subscript = subscript_part

    # Join remaining parts if any
    if len(parts) > 2:
        remaining = "_".join(parts[2:])
        return f"{main_name}$_{{{formatted_subscript}}}$_{remaining}"
    return f"{main_name}$_{{{formatted_subscript}}}$"


def format_units_for_plotting(units: str) -> str:
    """Convert verbose units to concise plotting format.

    Translates full unit names to standard abbreviations commonly
    used in oceanographic plots and publications.

    Parameters
    ----------
    units : str
        Full unit string (e.g., from netCDF attributes).

    Returns
    -------
    str
        Abbreviated unit string suitable for plot labels.

    Examples
    --------
    >>> format_units_for_plotting("Sverdrup")
    'Sv'
    >>> format_units_for_plotting("degrees_north")
    '°N'
    >>> format_units_for_plotting("degrees_Celsius")
    '°C'

    """
    unit_mappings = {
        "Sverdrup": "Sv",
        "sverdrup": "Sv",
        "degree_north": "°N",
        "degrees_north": "°N",
        "degree_south": "°S",
        "degrees_south": "°S",
        "degree_east": "°E",
        "degrees_east": "°E",
        "degree_west": "°W",
        "degrees_west": "°W",
        "degree_C": "°C",
        "degree_celsius": "°C",
        "degree_Celsius": "°C",
        "degrees_Celsius": "°C",
        "degrees C": "°C",
        "deg C": "°C",
        "meters": "m",
        "meter": "m",
        "seconds": "s",
        "m s-1": "m/s",
        "Sverdrup/m": "Sv/m",
        "sverdrup m-1": "Sv/m",
        "Sverdrup m-1": "Sv/m",
        "second": "s",
        "PetaWatts": "PW",
        "petawatts": "PW",
        "PW": "PW",
        "kg m-3": "kg/m³",
        "kg/m3": "kg/m³",
        "kg m^-3": "kg/m³",
    }

    return unit_mappings.get(units, units)


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
        raise TypeError("Input data must be a file path (str) or an xarray Dataset")
    if content_type in ["attributes", "attrs"]:
        if isinstance(data, (str, xr.Dataset)):
            return show_attributes(data)
        raise TypeError(
            "Attributes can only be shown for netCDF files (str) or xarray Datasets",
        )
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

    def get_attr(key: str) -> str:
        """Get attribute value based on data type."""
        if isinstance(data, str):
            return getattr(rootgrp, key)
        return data.attrs[key]

    if isinstance(data, str):
        print(f"information is based on file: {data}")
        rootgrp = Dataset(data, "r", format="NETCDF4")
        attributes = rootgrp.ncattrs()
    elif isinstance(data, xr.Dataset):
        print("information is based on xarray Dataset")
        attributes = data.attrs.keys()
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
    """Resample to monthly mean if time is datetime-like and spacing ~monthly.
    If time is float-year, just pass through as-is (no interpolation).
    """
    # find time coordinate
    time_key = [c for c in da.coords if c.lower() == "time"]
    if not time_key:
        raise ValueError("No time coordinate found.")
    time_key = time_key[0]

    time_values = da[time_key].values

    if np.issubdtype(time_values.dtype, np.datetime64):
        # compute spacing in days
        dt_days = np.nanmean(np.diff(time_values) / np.timedelta64(1, "D"))

        # already ~monthly? pass through
        if 20 <= dt_days <= 40:
            return da

        # otherwise resample
        mask_valid_time = ~np.isnat(time_values)
        da = da.isel({time_key: mask_valid_time})

        _, unique_indices = np.unique(da[time_key].values, return_index=True)
        da = da.isel({time_key: np.sort(unique_indices)})

        da = da.sortby(time_key)

        return da.resample({time_key: "1MS"}).mean()

    return da  # just return the original data without interpolation


def _format_units_for_plots(units: str) -> str:
    """Convert verbose unit names to abbreviated forms for plot labels.

    Parameters
    ----------
    units : str
        Original unit string

    Returns
    -------
    str
        Abbreviated unit string for plots

    """
    # Use the unit formatting function
    return format_units_for_plotting(units)


def plot_amoc_timeseries(
    data: list[xr.Dataset | xr.DataArray] | xr.Dataset | xr.DataArray,
    varnames: list[str] | None = None,
    labels: list[str] | None = None,
    colors: list[str] | None = None,
    title: str = "AMOC Time Series",
    ylabel: str | None = None,
    time_limits: tuple[str | pd.Timestamp, str | pd.Timestamp] | None = None,
    ylim: tuple[float, float] | None = None,
    figsize: tuple[float, float] = (10, 3),
    resample_monthly: bool = True,
    plot_raw: bool = True,
    lat_idx: int | None = None,
    region_idx: int | None = None,
    posterior_stat: str = "mean",  # "mean" or "median"
) -> tuple[plt.Figure, plt.Axes]:
    """Plot original and optionally monthly-averaged AMOC time series for one or more datasets.

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
    lat_idx : int, optional
        Latitude index to select when dataset has a 'lat' dimension.
        Required if dataset contains 'lat' dimension with posterior samples.
    region_idx : int, optional
        Region index to select when dataset has a 'number_regions' dimension.
        Required if dataset contains 'number_regions' dimension with posterior samples.
    posterior_stat : str, default "mean"
        Statistic to use when collapsing posterior samples dimension.
        Options are "mean" or "median".

    """
    if not isinstance(data, list):
        data = [data]

    if varnames is None:
        varnames = [None] * len(data)
    if labels is None:
        labels = [f"Dataset {i + 1}" for i in range(len(data))]
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

        dims = da.dims

        # MHT(lat, time, posterior_samples)
        if "posterior_samples" in dims:
            if "lat" in dims and lat_idx is None:
                raise ValueError("Dataset has 'lat'. Please provide lat_idx.")
            if "number_regions" in dims and region_idx is None:
                raise ValueError(
                    "Dataset has 'number_regions'. Please provide region_idx."
                )

            if "lat" in dims:
                da = da.isel(lat=lat_idx)
            if "number_regions" in dims:
                da = da.isel(number_regions=region_idx)

            # collapse posterior samples
            if posterior_stat == "mean":
                da = da.mean("posterior_samples")
            elif posterior_stat == "median":
                da = da.median("posterior_samples")
            else:
                raise ValueError("posterior_stat must be 'mean' or 'median'.")

        # Identify the time coordinate
        for coord in da.coords:
            if coord.lower() == "time":
                time_key = coord
                break
        else:
            raise ValueError("No time coordinate found in dataset.")

        # Raw plot
        if plot_raw:
            # Use grey if monthly resampling is enabled, otherwise the specified color
            raw_color = "grey" if resample_monthly else color
            ax.plot(
                da[time_key],
                da,
                color=raw_color,
                alpha=0.85 if not resample_monthly else 0.5,
                linewidth=1 if not resample_monthly else 0.5,
                label=f"{label} (raw)",
            )

        # Monthly mean plot
        if resample_monthly:
            da_monthly = monthly_resample(da)

            ax.plot(
                da_monthly[time_key],
                da_monthly,
                color=color,
                linewidth=1.5,
                label=f"{label} Monthly Avg",
            )

        # Build ylabel if not set
        if ylabel is None:
            # Use long_name first, then standard_name, then variable name
            label_text = da.attrs.get(
                "long_name", da.attrs.get("standard_name", da.name or "Data")
            )
            # Format variable names with Greek characters, then wrap long labels.
            label_text = format_variable_name_for_plotting(label_text)
            label_text = _vlabel(label_text)

            units = da.attrs.get("units", "")
            if units:
                formatted_units = _format_units_for_plots(units)
                ylabel = f"{label_text} ({formatted_units})"
            else:
                ylabel = label_text

    # Horizontal zero line
    ax.axhline(0, color="black", linestyle="--", linewidth=0.5)

    # Styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(ylabel if ylabel else "Transport (Sv)")
    ax.legend(loc="best")
    ax.grid(True, linestyle="--", alpha=0.5)

    # Limits
    if time_limits:
        ax.set_xlim(pd.Timestamp(time_limits[0]), pd.Timestamp(time_limits[1]))
    if ylim:
        ax.set_ylim(ylim)

    plt.tight_layout()
    return fig, ax


def plot_monthly_anomalies(
    **kwargs,  # noqa: ANN003
) -> tuple[plt.Figure, list[plt.Axes]]:
    """Plot the monthly anomalies for various datasets.

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

    for i, (data, label, color) in enumerate(
        zip(datasets, labels, color_cycle, strict=False)
    ):
        time = data["TIME"]
        axes[i].plot(time, data, color=color, label=label)
        axes[i].axhline(0, color="black", linestyle="--", linewidth=0.5)
        axes[i].set_title(label)
        axes[i].set_ylabel("Transport (Sv)")
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


# ------------------------------------------------------------------------------------
# PyGMT Publication Plotting Functions
# ------------------------------------------------------------------------------------

# Initialize PyGMT availability flag
HAS_PYGMT = False

# Check for PyGMT availability
try:
    import pygmt

    HAS_PYGMT = True
except Exception:  # noqa: BLE001
    # Catch all exceptions including ImportError, OSError, GMTCLibNotFoundError, etc.
    # Using broad exception handling here because PyGMT can fail in various unpredictable ways
    HAS_PYGMT = False


def _check_pygmt() -> None:
    """Check if PyGMT is available and raise informative error if not."""
    if not HAS_PYGMT:
        raise ImportError(
            "PyGMT is required for publication-quality plots. "
            "Install with: pip install pygmt\n"
            "Note: PyGMT requires GMT to be installed separately. "
            "See https://www.pygmt.org/latest/install.html for details."
        )


def _add_amocatlas_timestamp(fig: object) -> None:
    """Add standardized AMOCatlas timestamp to PyGMT figure.

    Parameters
    ----------
    fig : pygmt.Figure
        PyGMT figure to add timestamp to.

    """
    fig.timestamp(
        label="AMOCatlas", font="10p,Helvetica,gray30", timefmt="%Y-%m-%dT%H:%M"
    )


def plot_moc_timeseries_pygmt(
    df: pd.DataFrame, column: str = "moc", label: str = "MOC (Sv)"
) -> "pygmt.Figure":
    """Plot MOC time series using PyGMT with publication-quality styling.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'time_num' (decimal years) and data columns.
    column : str, default "moc"
        Name of the column to plot.
    label : str, default "MOC (Sv)"
        Y-axis label for the plot.

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    """
    _check_pygmt()

    fig = pygmt.Figure()

    pygmt.config(
        FONT_ANNOT_PRIMARY="20p",  # tick labels
        FONT_LABEL="20p",  # axis labels
        FONT_TITLE="20p",  # title (if used)
        MAP_TICK_LENGTH_PRIMARY="6p",  # major ticks longer
        MAP_TICK_PEN_PRIMARY="1.2p",  # major ticks thicker
        MAP_LABEL_OFFSET="10p",  # spacing axis ↔ label
        MAP_TICK_LENGTH_SECONDARY="3p",  # minor ticks longer
        MAP_TICK_PEN_SECONDARY="0.8p",  # minor ticks thicker
        MAP_GRID_PEN="0.25p,gray70,10_5",  # fine dashed grid
    )

    # --- Define plotting region ---
    col_filtered = f"{column}_filtered"
    xmax = max(df["time_num"].max(), 2025)
    if col_filtered not in df.columns:
        df[col_filtered] = df[column]
    ymin = df[[column, col_filtered]].min().min()
    ymax = df[[column, col_filtered]].max().max()
    region = [df["time_num"].min(), xmax, ymin, ymax]

    # --- Basemap ---
    fig.basemap(
        region=region, projection="X25c/7c", frame=["xaf", f"yafg10f5+l{label}", "WS"]
    )

    # --- Plot original series ---
    fig.plot(x=df["time_num"], y=df[column], pen=".75p,red", label="Original")

    # --- Plot filtered: thick white background + black foreground ---
    fig.plot(x=df["time_num"], y=df[col_filtered], pen="3.5p,white")
    fig.plot(
        x=df["time_num"], y=df[col_filtered], pen="2.5p,black", label="Filtered (Tukey)"
    )

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_osnap_components_pygmt(data: DataFrame | dict) -> "pygmt.Figure":
    """Plot OSNAP MOC components with shaded error bands using PyGMT.

    Parameters
    ----------
    data : pandas.DataFrame or dict
        Must contain:
        - time_num (decimal years)
        - MOC_SIGMA0, MOC_EAST_SIGMA0, MOC_WEST_SIGMA0 (or legacy MOC_ALL, MOC_EAST, MOC_WEST)
        - MOC_EAST_SIGMA0_ERR, MOC_WEST_SIGMA0_ERR (or legacy MOC_EAST_ERR, MOC_WEST_ERR)

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    """
    import pandas as pd

    _check_pygmt()

    # Convert to DataFrame if needed
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Translate OSNAP variable names to internal names for plotting
    var_mapping = {
        "MOC_SIGMA0": "MOC_ALL",
        "MOC_EAST_SIGMA0": "MOC_EAST",
        "MOC_WEST_SIGMA0": "MOC_WEST",
        "MOC_EAST_SIGMA0_ERR": "MOC_EAST_ERR",
        "MOC_WEST_SIGMA0_ERR": "MOC_WEST_ERR",
    }

    # Rename columns if needed
    for actual_name, internal_name in var_mapping.items():
        if actual_name in df.columns and internal_name not in df.columns:
            df[internal_name] = df[actual_name]

    fig = pygmt.Figure()

    # Styling
    pygmt.config(
        FONT_ANNOT_PRIMARY="20p",
        FONT_LABEL="20p",
        FONT_TITLE="20p",
        MAP_TICK_LENGTH_PRIMARY="6p",
        MAP_TICK_PEN_PRIMARY="1.2p",
        MAP_LABEL_OFFSET="10p",
        MAP_TICK_LENGTH_SECONDARY="3p",
        MAP_TICK_PEN_SECONDARY="0.8p",
        MAP_GRID_PEN="0.25p,gray70,10_5",
    )

    # Region
    xmax = max(df["time_num"].max(), 2022)
    ymin = df[["MOC_ALL", "MOC_EAST", "MOC_WEST"]].min().min() - 1
    ymax = df[["MOC_ALL", "MOC_EAST", "MOC_WEST"]].max().max() + 1
    ymin = min(ymin, -5)
    ymax = max(ymax, 30)
    region = [df["time_num"].min(), xmax, ymin, ymax]

    # Basemap
    fig.basemap(
        region=region, projection="X15c/7c", frame=["xaf", "yafg5f2+lMOC (Sv)", "WS"]
    )

    # --- Shaded error for EAST ---
    east_upper = df["MOC_EAST"] + df["MOC_EAST_ERR"]
    east_lower = df["MOC_EAST"] - df["MOC_EAST_ERR"]

    # Build filled polygon for EAST
    import numpy as np

    x_east = np.concatenate([df["time_num"], df["time_num"][::-1]])
    y_east = np.concatenate([east_upper, east_lower[::-1]])
    fig.plot(x=x_east, y=y_east, fill="orange", transparency=70, close=True)

    # --- Shaded error for WEST ---
    west_upper = df["MOC_WEST"] + df["MOC_WEST_ERR"]
    west_lower = df["MOC_WEST"] - df["MOC_WEST_ERR"]
    x_west = np.concatenate([df["time_num"], df["time_num"][::-1]])
    y_west = np.concatenate([west_upper, west_lower[::-1]])
    fig.plot(x=x_west, y=y_west, fill="blue", transparency=70, close=True)

    # --- Main curves ---
    fig.plot(x=df["time_num"], y=df["MOC_ALL"], pen="2.5p,black", label="Total")
    fig.plot(
        x=df["time_num"],
        y=df["MOC_EAST"],
        pen="2.5p,orange",
        label="East",
        transparency=20,
    )
    fig.plot(x=df["time_num"], y=df["MOC_WEST"], pen="2.5p,blue", label="West")

    # Legend
    fig.legend(position="JMR+jMR+o-1.5i/0i", box=True)

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_rapid_components_pygmt(df: pd.DataFrame) -> "pygmt.Figure":
    """Plot RAPID MOC and component transports using PyGMT.

    Parameters
    ----------
    df : pandas.DataFrame
        Must include:
        - 'time_num'
        - 'moc_mar_hc10' (total MOC)
        - 't_gs10' (Florida Current)
        - 't_ek10' (Ekman)
        - 't_umo10' (upper mid-ocean)

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    """
    _check_pygmt()

    fig = pygmt.Figure()

    pygmt.config(
        FONT_ANNOT_PRIMARY="20p",
        FONT_LABEL="20p",
        FONT_TITLE="20p",
        MAP_TICK_LENGTH_PRIMARY="6p",
        MAP_TICK_PEN_PRIMARY="1.2p",
        MAP_LABEL_OFFSET="10p",
        MAP_TICK_LENGTH_SECONDARY="3p",
        MAP_TICK_PEN_SECONDARY="0.8p",
        MAP_GRID_PEN="0.25p,gray70,10_5",
    )

    # Set region based on full value range
    xmax = max(df["time_num"].max(), 2025)
    components = ["moc_mar_hc10", "t_gs10", "t_ek10", "t_umo10"]
    ymin = df[components].min().min() - 1
    ymax = df[components].max().max() + 1
    region = [df["time_num"].min(), xmax, ymin, ymax]

    # Basemap
    fig.basemap(
        region=region,
        projection="X25c/15c",
        frame=["xaf", "yafg5f2+lTransport (Sv)", "WS+tRAPID MOC Components"],
    )

    # Plot each component with custom colors
    fig.plot(x=df["time_num"], y=df["moc_mar_hc10"], pen="1.5p,red", label="MOC")
    fig.plot(x=df["time_num"], y=df["t_gs10"], pen="1.5p,blue", label="Florida Current")
    fig.plot(x=df["time_num"], y=df["t_ek10"], pen="1.5p,black", label="Ekman")
    fig.plot(
        x=df["time_num"], y=df["t_umo10"], pen="1.5p,magenta", label="Upper Mid-Ocean"
    )

    # Plot labels at end of time series with slight offset

    # Use the actual end date of the time series
    x_label = df["time_num"].max()

    y_labels = {
        "MOC": df["moc_mar_hc10"].mean(),
        "Florida Current": df["t_gs10"].mean(),
        "Ekman": df["t_ek10"].mean(),
        "Upper Mid-Ocean": df["t_umo10"].mean(),
    }
    colors = {
        "MOC": "red",
        "Florida Current": "blue",
        "Ekman": "black",
        "Upper Mid-Ocean": "magenta",
    }
    for label, y in y_labels.items():
        fig.text(
            x=x_label,
            y=y,
            text=label,
            font=f"18p,Helvetica,{colors[label]}",
            justify="LM",
            no_clip=True,
            offset="0.1i/0i",  # Offset 0.1 inches to the right
        )

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_all_moc_pygmt(
    osnap_df: pd.DataFrame,
    rapid_df: pd.DataFrame,
    move_df: pd.DataFrame,
    samba_df: pd.DataFrame,
    filtered: bool = False,
) -> "pygmt.Figure":
    """Plot all MOC time series (OSNAP, RAPID, MOVE, SAMBA) in a stacked PyGMT figure.

    Parameters
    ----------
    osnap_df : pandas.DataFrame
        OSNAP MOC data with 'time_num' and 'moc'/'moc_filtered'.
    rapid_df : pandas.DataFrame
        RAPID MOC data with 'time_num' and 'moc'/'moc_filtered'.
    move_df : pandas.DataFrame
        MOVE MOC data with 'time_num' and 'moc'/'moc_filtered'.
    samba_df : pandas.DataFrame
        SAMBA MOC data with 'time_num' and 'moc'/'moc_filtered'.
    filtered : bool, default False
        Whether to plot filtered data (True) or original data (False).

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    """
    _check_pygmt()

    magenta1 = "231/41/138"
    red1 = "227/26/28"
    blue1 = "8/104/172"
    green1 = "35/139/69"

    # Select column based on filtered flag
    col = "moc_filtered" if filtered else "moc"

    # Prepare data and labels
    dfs = [
        (osnap_df, "MOC (Sv)", (5, 25), 5, "OSNAP", green1, "W"),
        (rapid_df, "MOC (Sv)", (5, 30), 6, "RAPID 26°N", red1, "E"),
        (move_df, "MOC (Sv)", (5, 30), 6, "MOVE 16°N", magenta1, "W"),
        (samba_df, "Anomaly (Sv)", (-10, 15), 6, "SAMBA 34.5°S", blue1, "ES"),
    ]

    # Find global x range
    xmin = min(min(df["time_num"].min() for df, _, _, _, _, _, _ in dfs), 2000)
    xmax = max(max(df["time_num"].max() for df, _, _, _, _, _, _ in dfs), 2025)

    # Create figure
    fig = pygmt.Figure()

    panel_width = 20  # cm
    pygmt.config(
        FONT_ANNOT_PRIMARY="20p",
        FONT_LABEL="20p",
        FONT_TITLE="20p",
        MAP_TICK_LENGTH_PRIMARY="6p",
        MAP_TICK_PEN_PRIMARY="1.2p",
        MAP_LABEL_OFFSET="10p",
        MAP_TICK_LENGTH_SECONDARY="3p",
        MAP_TICK_PEN_SECONDARY="0.8p",
        MAP_GRID_PEN="0.25p,gray70,10_5",
    )

    # Set locations for labels
    myxloc = [2000.2, 2000.2, 2000.2, 2000.2]
    myyloc = [15, 17, 17, 0]
    myyoff = [0, 0, 8.5, -3]

    for i, (
        df,
        label,
        (ymin, ymax),
        panel_height,
        txt_lbl,
        pen_col,
        frame_coord,
    ) in enumerate(dfs):
        region = [xmin, xmax, ymin, ymax]

        fig.basemap(
            region=region,
            projection=f"X{panel_width}c/{panel_height}c",
            frame=["xaf", f"yaff5+l{label}", frame_coord],
        )

        # Plot reference line and data
        fig.plot(x=[xmin, xmax], y=[myyloc[i], myyloc[i]], pen="1.5p,gray50,2_2")

        if filtered:
            fig.plot(x=df["time_num"], y=df[col], pen="3.5p,white", no_clip=(i == 3))
            fig.plot(x=df["time_num"], y=df[col], pen="2p," + pen_col, no_clip=(i == 3))
        else:
            fig.plot(
                x=df["time_num"], y=df[col], pen="1.5p," + pen_col, no_clip=(i == 3)
            )

        # Add text annotation
        fig.text(
            text=txt_lbl,
            x=myxloc[i],
            y=myyloc[i] + myyoff[i] + 0.5,
            font="18p,Helvetica",
            justify="LB",
        )

        # Shift down for next panel, except after last
        if i < len(dfs) - 1:
            if i < 2:
                fig.shift_origin(yshift=f"-{panel_height - 1.5}c")
            else:
                fig.shift_origin(yshift=f"-{panel_height - 1.2}c")

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_bryden2005_pygmt() -> "pygmt.Figure":
    """Plot Bryden et al. 2005 historical AMOC estimates using PyGMT.

    Creates a plot of the historical AMOC estimates from Bryden et al. (2005)
    showing the decline from 1957 to 2004. This provides historical context
    for modern observational time series.

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    References
    ----------
    Bryden, H. L., Longworth, H. R., & Cunningham, S. A. (2005).
    Slowing of the Atlantic meridional overturning circulation at 25°N.
    Nature, 438(7068), 655-657.

    """
    _check_pygmt()

    import os

    import pandas as pd

    # Bryden 2005 data
    years = [1957, 1981, 1992, 1998, 2004]
    amoc_values = [22.9, 18.7, 19.4, 16.1, 14.8]
    xticks = [1957, 1970, 1981, 1992, 2004]
    xtick_labels = ["af", "af", "af", "af", "af"]

    # Write custom tick annotation file
    with open("custom_xticks.txt", "w") as f:
        for x, label in zip(xticks, xtick_labels, strict=False):
            f.write(f"{x} {label}\n")

    # Create DataFrame
    data = pd.DataFrame({"Year": years, "AMOC": amoc_values})

    # Create figure
    fig = pygmt.Figure()

    pygmt.config(
        FONT_ANNOT_PRIMARY="18p",  # tick labels
        FONT_LABEL="18p",  # axis labels
        FONT_TITLE="18p",  # title (if used)
        MAP_TICK_LENGTH_PRIMARY="6p",  # major ticks longer
        MAP_TICK_PEN_PRIMARY="1.2p",  # major ticks thicker
        MAP_LABEL_OFFSET="10p",  # spacing axis ↔ label
        MAP_TICK_LENGTH_SECONDARY="3p",  # minor ticks longer
        MAP_TICK_PEN_SECONDARY="0.8p",  # minor ticks thicker
        MAP_GRID_PEN="0.25p,gray70,10_5",  # fine dashed grid
    )

    # Set region and frame
    fig.basemap(
        region=[1955, 2006, 13, 24],
        projection="X8c/6c",
        frame=["WS", "yaf+lMOC (Sv)", "xccustom_xticks.txt"],
    )

    # Plot red line
    fig.plot(x=data["Year"], y=data["AMOC"], pen="2p,red")

    # Plot red diamonds (with black edge)
    fig.plot(x=data["Year"], y=data["AMOC"], style="d0.3c", fill="red", pen="red")

    # Delete the custom tick file
    if os.path.exists("custom_xticks.txt"):
        os.remove("custom_xticks.txt")

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_all_moc_overlaid_pygmt(
    osnap_df: pd.DataFrame,
    rapid_df: pd.DataFrame,
    move_df: pd.DataFrame,
    samba_df: pd.DataFrame,
    filtered: bool = False,
) -> "pygmt.Figure":
    """Plot all MOC time series overlaid using separate coordinate systems.

    This creates overlaid plots with different y-ranges for MOC data vs SAMBA anomaly,
    similar to the original moc_tseries_pygmt notebook with shiftflag=False.

    Parameters
    ----------
    osnap_df : pandas.DataFrame
        OSNAP MOC data with 'time_num' and 'moc'/'moc_filtered'.
    rapid_df : pandas.DataFrame
        RAPID MOC data with 'time_num' and 'moc'/'moc_filtered'.
    move_df : pandas.DataFrame
        MOVE MOC data with 'time_num' and 'moc'/'moc_filtered'.
    samba_df : pandas.DataFrame
        SAMBA MOC data with 'time_num' and 'moc'/'moc_filtered'.
    filtered : bool, default False
        Whether to plot filtered data (True) or original data (False).

    Returns
    -------
    pygmt.Figure
        PyGMT figure object.

    Raises
    ------
    ImportError
        If PyGMT is not installed.

    """
    _check_pygmt()

    # Color scheme matching original
    magenta1 = "231/41/138"
    red1 = "227/26/28"
    blue1 = "8/104/172"
    green1 = "35/139/69"

    # Select column based on filtered flag
    col = "moc_filtered" if filtered else "moc"

    # Prepare data and labels - overlay mode (shiftflag=False)
    dfs = [
        (osnap_df, "MOC (Sv)", (10, 20), 6, "OSNAP", green1, "W"),
        (rapid_df, "MOC (Sv)", (10, 20), 6, "RAPID 26°N", red1, "W"),
        (move_df, "MOC (Sv)", (10, 20), 6, "MOVE 16°N", magenta1, "W"),
        (samba_df, "Anomaly (Sv)", (-5, 5), 6, "SAMBA 34.5°S", blue1, "ES"),
    ]

    # Find global x range
    xmin = min(min(df["time_num"].min() for df, _, _, _, _, _, _ in dfs), 2000)
    xmax = max(max(df["time_num"].max() for df, _, _, _, _, _, _ in dfs), 2025)

    # Create figure
    fig = pygmt.Figure()

    panel_width = 20  # cm
    pygmt.config(
        FONT_ANNOT_PRIMARY="20p",
        FONT_LABEL="20p",
        FONT_TITLE="20p",
        MAP_TICK_LENGTH_PRIMARY="6p",
        MAP_TICK_PEN_PRIMARY="1.2p",
        MAP_LABEL_OFFSET="10p",
        MAP_TICK_LENGTH_SECONDARY="3p",
        MAP_TICK_PEN_SECONDARY="0.8p",
        MAP_GRID_PEN="0.25p,gray70,10_5",
    )

    # Label positions for overlay mode
    myxloc = [2018.2, 2006.2, 2000.2, 2015.2]
    myyloc = [13.5, 19, 15, 0]
    myyoff = [0, 0, -3, -4]

    for i, (
        df,
        label,
        (ymin, ymax),
        panel_height,
        txt_lbl,
        pen_col,
        frame_coord,
    ) in enumerate(dfs):
        region = [xmin, xmax, ymin, ymax]

        fig.basemap(
            region=region,
            projection=f"X{panel_width}c/{panel_height}c",
            frame=["xaf", f"yaff2+l{label}", frame_coord],
        )

        # Add gray horizontal line at y=0
        fig.plot(x=[xmin, xmax], y=[0, 0], pen="1.5p,gray50,2_2")

        # Plot the time series with white background + colored foreground
        fig.plot(x=df["time_num"], y=df[col], pen="3.5p,white", no_clip=True)
        fig.plot(x=df["time_num"], y=df[col], pen="2p," + pen_col, no_clip=True)

        # Add text annotation
        fig.text(
            text=txt_lbl,
            x=myxloc[i],
            y=myyloc[i] + myyoff[i] + 0.5,
            font=f"18p,Helvetica,{pen_col}",
            justify="LB",
            no_clip=True,
        )

        # No shifting between panels in overlay mode
        if i < len(dfs) - 1:
            fig.shift_origin(yshift=0)

    # Add AMOCatlas timestamp
    _add_amocatlas_timestamp(fig)

    return fig


def plot_amoc_2d_data(
    data: xr.Dataset | xr.DataArray,
    varname: str | None = None,
    title: str = "AMOC 2D Data",
    ylabel: str | None = None,
    time_limits: tuple[str | pd.Timestamp, str | pd.Timestamp] | None = None,
    ylim: tuple[float, float] | None = None,
    figsize: tuple[float, float] = (12, 6),
    colormap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot 2D AMOC data with time on x-axis and depth/other coordinate on y-axis.

    This function creates a color-filled contour plot suitable for visualizing
    2D oceanographic data such as MOC streamfunction vs depth and time, or
    temperature profiles over time.

    Parameters
    ----------
    data : xr.Dataset or xr.DataArray
        Dataset or DataArray containing 2D data to plot.
    varname : str, optional
        Variable name to extract from dataset. Not needed if DataArray is passed.
    title : str
        Title of the plot.
    ylabel : str, optional
        Label for the y-axis (vertical coordinate). If None, inferred from data attributes.
    time_limits : tuple of str or pd.Timestamp, optional
        X-axis time limits (start, end).
    ylim : tuple of float, optional
        Y-axis limits (min, max).
    figsize : tuple
        Size of the figure.
    colormap : str
        Colormap for the 2D data. Default is 'RdBu_r' (polar colormap).
    vmin : float, optional
        Minimum value for color scale. If None, inferred from data.
    vmax : float, optional
        Maximum value for color scale. If None, inferred from data.

    Returns
    -------
    tuple[plt.Figure, plt.Axes]
        The matplotlib figure and axes objects.

    Raises
    ------
    ValueError
        If data doesn't have the required dimensions or if TIME coordinate is missing.

    """
    # Extract DataArray if needed
    if isinstance(data, xr.Dataset):
        if varname is None:
            raise ValueError("varname must be specified when passing a Dataset")
        if varname not in data:
            raise ValueError(f"Variable '{varname}' not found in dataset")
        da = data[varname]
    else:
        da = data

    # Find time coordinate
    time_coord = None
    for coord in da.coords:
        if coord.lower() in ["time", "times"]:
            time_coord = coord
            break

    if time_coord is None:
        raise ValueError("No TIME coordinate found in data")

    # Find the other dimension (should be depth, level, etc.)
    dims = list(da.dims)
    dims.remove(time_coord)
    if len(dims) != 1:
        raise ValueError(
            f"Data must be 2D with TIME and one other dimension. Found dimensions: {da.dims}"
        )

    vertical_dim = dims[0]

    # Prioritize vertical coordinates in order: DEPTH, PRESSURE, SIGMA0, SIGMA2
    # Look for coordinates that match the vertical dimension
    vertical_coord = None
    coord_priority = ["DEPTH", "PRESSURE", "SIGMA0", "SIGMA2"]

    for coord_name in coord_priority:
        if coord_name in da.coords:
            coord = da.coords[coord_name]
            # Check if this coordinate has the same dimension as our vertical dimension
            if len(coord.dims) == 1 and coord.dims[0] == vertical_dim:
                vertical_coord = coord_name
                break

    # If no prioritized coordinate found, fall back to the dimension name
    if vertical_coord is None:
        vertical_coord = vertical_dim

    # Set up the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Determine color scale limits if not provided
    if vmin is None or vmax is None:
        data_finite = da.values[np.isfinite(da.values)]
        if len(data_finite) > 0:
            if vmin is None:
                vmin = np.percentile(data_finite, 2)
            if vmax is None:
                vmax = np.percentile(data_finite, 98)
        else:
            vmin, vmax = -1, 1

    # Create 2D contour plot
    im = da.plot.contourf(
        ax=ax,
        x=time_coord,
        y=vertical_coord,
        cmap=colormap,
        levels=50,
        vmin=vmin,
        vmax=vmax,
        add_colorbar=True,
        cbar_kwargs={"shrink": 0.8, "aspect": 20},
    )

    # Set colorbar label to use long_name [units] format
    if hasattr(im, "colorbar") and im.colorbar is not None:
        # Get label text from data variable attributes
        label_text = da.attrs.get(
            "long_name", da.attrs.get("standard_name", varname or "Data")
        )
        # Format variable names with Greek characters
        label_text = format_variable_name_for_plotting(label_text)

        units = da.attrs.get("units", "")
        if units:
            formatted_units = _format_units_for_plots(units)
            colorbar_label = f"{label_text} ({formatted_units})"
        else:
            colorbar_label = label_text
        im.colorbar.set_label(colorbar_label, fontsize=12)

    # Set labels and title
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time", fontsize=12)

    # Set y-axis label
    if ylabel is None:
        # Try to infer from coordinate attributes
        try:
            vertical_var = da.coords[vertical_coord]
            ylabel = vertical_var.attrs.get(
                "long_name",
                vertical_var.attrs.get("standard_name", vertical_coord.title()),
            )
            # Format variable names with Greek characters
            ylabel = format_variable_name_for_plotting(ylabel)

            # Add units if available
            units = vertical_var.attrs.get("units", "")
            if units:
                formatted_units = _format_units_for_plots(units)
                ylabel += f" ({formatted_units})"
        except KeyError:
            # Coordinate doesn't exist in dataset, use dimension name as fallback
            ylabel = format_variable_name_for_plotting(vertical_coord.title())

    ax.set_ylabel(ylabel, fontsize=12)

    # Apply axis limits if specified
    if time_limits is not None:
        ax.set_xlim(time_limits)

    if ylim is not None:
        ax.set_ylim(ylim)
    else:
        # For depth coordinates, invert y-axis (shallow at top)
        if (
            vertical_coord.lower() in ["depth", "z", "level"]
            or "depth" in ylabel.lower()
        ):
            ax.invert_yaxis()

    # Format time axis nicely
    fig.autofmt_xdate()

    # Add grid for better readability
    ax.grid(True, alpha=0.3)

    # Use AMOCatlas style if available, else fall back to matplotlib defaults
    with contextlib.suppress(OSError):
        plt.style.use("amocatlas.mplstyle")

    plt.tight_layout()

    return fig, ax
