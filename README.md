# AMOCarray

[![PyPI version](https://badge.fury.io/py/amocarray.svg)](https://badge.fury.io/py/amocarray)
[![Python](https://img.shields.io/pypi/pyversions/amocarray.svg)](https://pypi.org/project/amocarray/)
[![License](https://img.shields.io/github/license/AMOCcommunity/amocarray.svg)](LICENSE)

**Clean, modular loading of AMOC observing array datasets, with optional structured logging and metadata enrichment.**

AMOCarray provides a unified system to access and process data from major Atlantic Meridional Overturning Circulation (AMOC) observing arrays. The Atlantic Meridional Overturning Circulation is a critical component of Earth's climate system, transporting heat northward in the Atlantic Ocean. This project enables researchers to easily access, analyze, and visualize data from key monitoring stations.

This is a work in progress, all contributions welcome!

## Table of Contents
- [Features](#features)
- [Supported Arrays](#supported-arrays)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Development](#development)
- [Funding & Support](#funding--support)
- [Acknowledgements](#acknowledgements)
- [Contributing](#contributing)

## Features

- 🌊 **Unified Data Access**: Single interface for multiple AMOC observing arrays
- 📊 **Automatic Data Download**: Intelligent caching system prevents redundant downloads
- 📝 **Structured Logging**: Per-dataset logging for reproducible workflows
- 🔍 **Metadata Enrichment**: Enhanced datasets with processing timestamps and source information
- 📈 **Visualization Tools**: Built-in plotting functions with consistent styling
- 🧪 **Sample Datasets**: Quick access to example data for testing and development

## Supported Arrays

| Array | Location | Description |
|-------|----------|-------------|
| **RAPID** | 26°N | Continuous monitoring since 2004 |
| **MOVE** | 16°N | Meridional heat transport |
| **OSNAP** | Subpolar North Atlantic | Overturning circulation |
| **SAMBA** | 34.5°S | South Atlantic MOC |
| **MOCHA** | Various | Historical datasets |
| **41°N** | 41°N | North Atlantic section |
| **DSO** | Denmark Strait | Overflow monitoring |

## Installation

### From PyPI (Recommended)
```bash
pip install amocarray
```

**Requirements**: Python ≥3.9, with numpy, pandas, xarray, and matplotlib.

### For Development
```bash
git clone https://github.com/AMOCcommunity/amocarray.git
cd amocarray
pip install -r requirements-dev.txt
pip install -e .
```

This installs amocarray locally. The `-e` ensures that any edits you make in the files will be picked up by scripts that import functions from amocarray.

## Quick Start

### Load Sample Data
```python
from amocarray import readers

# Load RAPID sample dataset
ds = readers.load_sample_dataset("rapid")
print(ds)
```

### Load Full Datasets
```python
from amocarray import readers

# Load complete dataset (downloads and caches data)
datasets = readers.load_dataset("osnap")
for ds in datasets:
    print(ds)
```

A `*.log` file will be written to `logs/` by default.

Data will be cached in `~/.amocarray_data/` unless you specify a custom location.

## Documentation

Documentation is available at [https://amoccommunity.github.io/amocarray](https://amoccommunity.github.io/amocarray/).

Check out the demo notebook `notebooks/demo.ipynb` for example functionality.

## Project Structure

```
amocarray/
│
├── readers.py               # Orchestrator for loading datasets
├── read_move.py             # MOVE reader
├── read_rapid.py            # RAPID reader
├── read_osnap.py            # OSNAP reader
├── read_samba.py            # SAMBA reader
├── read_mocha.py            # MOCHA reader
├── read_41n.py              # 41°N reader
├── read_dso.py              # DSO reader
├── read_fw2015.py           # Frajka-Williams 2015 reader
│
├── utilities.py             # Shared utilities (downloads, parsing, etc.)
├── logger.py                # Structured logging setup
├── plotters.py              # Visualization functions
├── tools.py                 # Analysis and calculation functions
├── standardise.py           # Common formatting and metadata
├── writers.py               # Data export functionality
│
└── tests/                   # Unit tests
```

## Development

### Running Tests
All new functions should include tests. You can run tests locally and generate a coverage report with:
```bash
pytest --cov=amocarray --cov-report term-missing tests/
```

Try to ensure that all the lines of your contribution are covered in the tests.

### Code Quality
```bash
black amocarray/ tests/          # Format code
ruff check amocarray/ tests/     # Lint code
pre-commit run --all-files       # Run all hooks
```

### Working with Notebooks
You can run the example jupyter notebook by launching jupyterlab with `jupyter-lab` and navigating to the `notebooks` directory, or in VS Code or another python GUI.

### Documentation
To build the documentation locally you need to install a few extra requirements:

- Install `make` for your computer, e.g. on ubuntu with `sudo apt install make`
- Install the additional python requirements. Activate the environment you use for working with amocarray, navigate to the top directory of this repo, then run `pip install -r requirements-dev.txt`

Once you have the extras installed, you can build the docs locally by navigating to the `docs/` directory and running `make clean html`. This command will create a directory called `build/` which contains the html files of the documentation. Open the file `docs/build/html/index.html` in your browser, and you will see the docs with your changes applied.

## Funding & Support

<div align="center">
  <img src="docs/source/_static/epoc-logo.jpg" alt="EPOC Logo" width="300"/>
</div>

This project is supported by the Horizon Europe project **EPOC - Explaining and Predicting the Ocean Conveyor** (Grant Agreement No. 101081012).

*Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.*

## Roadmap

- [ ] Add test coverage for utilities and readers
- [ ] Add dataset summary output at end of load_dataset()
- [x] Optional global logging helpers (disable_logging(), enable_logging())
- [ ] Extend load_sample_dataset() to support all arrays
- [x] Metadata enrichment (source paths, processing dates)
- [ ] Clarify separation between added metadata and original metadata

## Acknowledgements

The observing arrays and datasets accessed through AMOCarray are supported by:

- **RAPID data**: The RAPID-MOC monitoring project is funded by the Natural Environment Research Council (UK). Data is freely available from [www.rapid.ac.uk](https://www.rapid.ac.uk/)

- **MOVE data**: The MOVE project is funded by the NOAA Climate Program Office under award NA15OAR4320071. Initial funding came from the German Bundesministerium für Bildung und Forschung. Data collection is carried out by Uwe Send and Matthias Lankhorst at Scripps Institution of Oceanography

- **OSNAP data**: OSNAP data were collected and made freely available by the OSNAP (Overturning in the Subpolar North Atlantic Program) project and all the national programs that contribute to it ([www.o-snap.org](https://www.o-snap.org)). Multiple contributing institutions from US, UK, Germany, Netherlands, Canada, France, and China

- **SAMBA data**: SAMBA data were collected and made freely available by the SAMOC international project and contributing national programs

- **MOCHA data**: Data from the RAPID-MOCHA program are funded by the U.S. National Science Foundation and U.K. Natural Environment Research Council

- **41°N data**: These data were collected and made freely available by the International Argo Program and the national programs that contribute to it. The Argo Program is part of the Global Ocean Observing System

- **DSO data**: Generated by Institution of Oceanography Hamburg and Marine and Freshwater Research Institute (Reykjavik, Iceland). Supported through funding from NACLIM (EU-FP7, grant 308299), RACE II, RACE-Synthese (German BMBF), Nordic WOCE, VEINS, MOEN, ASOF-W, NAClim, THOR, AtlantOS, and Blue Action

- **FW2015 data**: Based on Frajka-Williams, E. (2015), "Estimating the Atlantic overturning at 26°N using satellite altimetry and cable measurements"

Dataset access and processing via [AMOCarray](https://github.com/AMOCcommunity/amocarray).

## Contributing

All contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Initial Plans

The **initial plan** for this repository is to simply load the volume transports as published by different AMOC observing arrays and replicate (update) the figure from Frajka-Williams et al. (2019) [10.3389/fmars.2019.00260](https://doi.org/10.3389/fmars.2019.00260).

<img width="358" alt="AMOC transport comparison" src="https://github.com/user-attachments/assets/fb35a276-a41e-4cef-b78f-9c3c46710466" />

---

*For questions or support, please open an [issue](https://github.com/AMOCcommunity/amocarray/issues) or check our [documentation](https://amoccommunity.github.io/amocarray/).*