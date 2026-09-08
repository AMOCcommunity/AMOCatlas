"""AMOCatlas: Atlantic Meridional Overturning Circulation Data Access.

AMOCatlas provides unified access to data from major AMOC observing arrays
including RAPID, OSNAP, MOVE, SAMBA, and others. The package standardizes
data formats, provides analysis tools, and enables consistent visualization
across different monitoring systems.

Key Features:
- Unified data loading interface for multiple AMOC arrays
- Automatic data download and caching
- Standardized metadata and data formats
- Visualization tools including PyGMT publication figures
- Analysis functions for filtering and processing time series

Basic Usage:
    >>> from amocatlas import read
    >>> data = read.rapid()                    # Single transport dataset
    >>> osnap = read.osnap(version="2025")     # Latest OSNAP data
    >>> all_data = read.rapid(all_files=True)  # All RAPID files as list

    # Legacy API (still supported but deprecated):
    >>> from amocatlas import readers
    >>> datasets = readers.load_dataset("rapid")  # deprecated
    >>> sample_data = readers.load_sample_dataset("osnap")  # deprecated
"""

# Import core modules to make them available at package level
from . import (
    compliance_checker,
    convert,
    data_sources,  # New data sources package
    logger,
    plotters,
    read,  # New intuitive API namespace
    reader_utils,
    readers,
    standardise,
    tools,
    utilities,
    writers,
)

# Version information
from ._version import __version__

# Import key utilities at top level for convenience
from .utilities import get_data_dir, set_data_dir

__all__ = [
    "readers",
    "read",
    "plotters",
    "standardise",
    "utilities",
    "tools",
    "logger",
    "writers",
    "convert",
    "compliance_checker",
    "reader_utils",
    "data_sources",
    "set_data_dir",
    "get_data_dir",
    "__version__",
]
