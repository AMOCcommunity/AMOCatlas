# AMOCatlas


[![PyPI version](https://img.shields.io/pypi/v/AMOCatlas.svg)](https://pypi.org/project/AMOCatlas/)
[![Python](https://img.shields.io/pypi/pyversions/AMOCatlas.svg)](https://pypi.org/project/AMOCatlas/)
[![License](https://img.shields.io/github/license/AMOCcommunity/amocatlas.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21921671.svg)](https://doi.org/10.5281/zenodo.21921671)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://amoccommunity.github.io/amocatlas/)

**One Python API for loading and comparing AMOC transport datasets — from moored observing arrays to satellite/Argo-based estimates — with consistent variable names, units, and metadata.**

AMOCatlas provides unified access to data on the Atlantic Meridional Overturning Circulation (AMOC), which transports heat northward in the Atlantic and is a key component of the climate system. It spans both in-situ observing arrays (RAPID, OSNAP, MOVE, SAMBA, …) and blended or estimation-based products (satellite altimetry, Argo, and reanalysis-derived estimates). Instead of hand-parsing a different file format for each source, you load any of 20 datasets through one interface and get back standardised, analysis-ready `xarray` datasets.

AMOCatlas does not alter the underlying data. It re-serves the same values as the source publications, adding standardised units, variable names, attribution, and provenance metadata — so the numbers you analyse are the numbers you would cite from the original dataset.

<div align="center">
  <img src="docs/source/_static/paperfigs/amoc_multi_array_overlaid.png" alt="Atlantic Meridional Overturning Circulation time series from multiple observing arrays plotted on the same coordinate system: OSNAP (subpolar North Atlantic), RAPID (26°N), MOVE (16°N) and SAMBA (34.5°S), showing MOC transport in Sverdrups across Atlantic latitudes." width="600"/>
  <br/>
  <em>AMOC transport from OSNAP, RAPID (26°N), MOVE (16°N) and SAMBA (34.5°S) — loaded and plotted through AMOCatlas.</em>
</div>

This is a work in progress, all contributions welcome!

## Table of Contents
- [Features](#features)
- [Supported Arrays](#supported-arrays)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Citing](#citing)
- [Development](#development)
- [Funding & Support](#funding--support)
- [Acknowledgements](#acknowledgements)
- [Contributing](#contributing)

## Features

- 🌊 **Unified Data Access**: Single interface for multiple AMOC observing arrays
- 📊 **Automatic Data Download**: Local caching avoids redundant downloads
- 📝 **Structured Logging**: Per-dataset logging for reproducible workflows
- 🔍 **Metadata Enrichment**: Enhanced datasets with processing timestamps and source information
- 📈 **Visualization Tools**: Built-in plotting functions with consistent styling
- 🧪 **Sample Datasets**: Quick access to example data for testing and development

## Available Data Sources

AMOCatlas serves two kinds of source, distinguished below. **Observing arrays** are direct in-situ measurements from moored instruments; **blended/estimated products** derive transports from satellite altimetry, Argo, XBT, or statistical methods. Both are served through the same `read.<name>()` interface.

### Observing arrays (in-situ)

| Data Source | Location | Description | Read Command |
|-------------|----------|-------------|--------------|
| **Arctic Gateway** | Arctic Ocean | Pan-Arctic gateway transports | `read.arcticgateway()` |
| **DSO** | Denmark Strait | Overflow transport | `read.dso()` |
| **FBC** | Faroe Bank Channel | Overflow transport monitoring | `read.fbc()` |
| **OSNAP** | Subpolar North Atlantic | Meridional overturning since 2014 | `read.osnap()` |
| **SCOTIA** | Scotland–Canada | Overturning in neutral-density space, subpolar North Atlantic | `read.scotia()` |
| **RAPID** | 26°N | MOC and overturning transports since 2004 | `read.rapid()` |
| **MOCHA** | 26°N | Meridional heat transport since 2004 | `read.mocha()` |
| **MOVE** | 16°N | Meridional overturning since 2001 | `read.move()` |
| **SAMBA** | 34.5°S | South Atlantic MOC *anomaly* | `read.samba()` |

### Blended / estimated products

| Data Source | Location | Description | Read Command |
|-------------|----------|-------------|--------------|
| **CALAFAT2025** | Atlantic | Bayesian estimates of Atlantic meridional heat transport spanning latitudes | `read.calafat2025()` |
| **ZHENG2024** | Atlantic | Observation-based Atlantic meridional freshwater transport spanning latitudes | `read.zheng2024()` |
| **NAC** | Atlantic | North Atlantic Current from satellite and float observations | `read.nac()` |
| **OVIDE** | Greenland–Portugal (A25) | MOC intensity across the A25 OVIDE line (altimetry + Argo/ISAS) | `read.ovide()` |
| **NOAC 47°N** | 47°N | North Atlantic Ocean Current MOC | `read.noac47n()` |
| **41°N Array** | 41°N | Meridional overturning from Argo + altimetry | `read.wh41n()` |
| **LEBRAS35N** | 35°N | Meridional overturning at 35°N from deep moorings, floats, and satellite altimeter | `read.lebras35n()` |
| **FW2015** | 26°N | Frajka-Williams 2015 satellite–cable estimate at 26°N | `read.fw2015()` |
| **SF2021** | 26°N | Meridional overturning estimate at 26°N from satellite altimetry | `read.sf2021()` |
| **AXMOC22.5S** | 22.5°S | Estimates of AMOC and heat transport at 22.5°S | `read.axmoc22s()` |
| **AXMOC34.5S** | 34.5°S | Estimates of AMOC, heat and freshwater transports at 34.5°S | `read.axmoc34s()` |

For more detail on the AMOC and observing arrays, see: 

  - UCAR overview: https://climatedataguide.ucar.edu/climate-data/observations-atlantic-meridional-overturning-circulation-amoc
  - AtlantOS/OceanSITES: https://www.ocean-ops.org/oceansites/tma/index.html

## Installation

### From PyPI (Recommended)
```bash
pip install AMOCatlas
```

**Requirements**: Python ≥3.10, with numpy, pandas, xarray, and matplotlib.

### For Development
```bash
git clone https://github.com/AMOCcommunity/amocatlas.git
cd amocatlas
pip install -e ".[dev]"
```

This installs amocatlas locally. The `-e` ensures that any edits you make in the files will be picked up by scripts that import functions from amocatlas.

## Quick Start

The `read` namespace returns a single standardised `xarray` dataset per array, downloading and caching on the first call:

```python
from amocatlas import read

ds = read.rapid()  # RAPID transport at 26°N
print(ds)

osnap = read.osnap()  # OSNAP; uses the latest version by default
```

Common options:

```python
read.osnap(version="2025")  # select a version where multiple exist
read.rapid(all_files=True)  # list of all files for an array, not just the standard one
read.rapid(raw=True)  # original upstream format, without standardisation
```

The legacy string-based API and small bundled samples remain available:

```python
from amocatlas import readers

ds = readers.load_sample_dataset("rapid")  # small bundled sample, no download
datasets = readers.load_dataset("rapid")  # returns a list of datasets
```

**Data location and logs.** Downloads are cached in `~/.amocatlas_data/` and a per-run `*.log` is written to `logs/`. Override the cache per call with `data_dir="/path/to/data"`, or set a default:

```python
import amocatlas

amocatlas.set_data_dir("~/my_data")  # custom location
print(amocatlas.get_data_dir())
```

The `set_data_dir("project")` shortcut (use `project/data`) only works from a source checkout (`pip install -e .`); regular installs need an explicit path.

For the full API, see the [documentation](https://amoccommunity.github.io/AMOCatlas/).


## Documentation

Documentation is available at [https://amoccommunity.github.io/AMOCatlas](https://amoccommunity.github.io/AMOCatlas/).

Check out the demo notebook `notebooks/demo.ipynb` for example functionality.

## Citing

AMOCatlas serves data collected and published by others. If it supports your work, please cite **both**:

1. **The original observing array(s) you used.** Each dataset has its own reference and acknowledgement — see [Acknowledgements](#acknowledgements) and the per-array documentation. The scientific credit belongs to the teams who collect, quality-control, and publish these measurements.

2. **AMOCatlas**, if the tooling itself was useful, via its archived release:

   > Frajka-Williams, E. and Schmitz, I. (2026). *amocatlas* (v0.4.0). Zenodo. https://doi.org/10.5281/zenodo.21921671

The DOI [10.5281/zenodo.21921671](https://doi.org/10.5281/zenodo.21921671) always resolves to the latest release; see [CITATION.cff](CITATION.cff) for the machine-readable citation and version-specific details.

## Project Structure

```
amocatlas/
│
├── read.py                  # 🆕 Modern API namespace (read.rapid(), read.osnap(), etc.)
├── readers.py               # Legacy orchestrator for loading datasets
├── reader_utils.py          # Shared utilities for all data source readers
│
├── data_sources/            # 🆕 Organized data source readers
│   ├── rapid26n.py          # RAPID array (26°N)
│   ├── move16n.py           # MOVE array (16°N)
│   ├── osnap55n.py          # OSNAP array (Subpolar North Atlantic)
│   ├── samba34s.py          # SAMBA array (34.5°S)
│   ├── mocha26n.py          # MOCHA dataset (26°N)
│   ├── wh41n.py             # 41°N array
│   ├── dso.py               # DSO overflow
│   ├── fbc.py               # Faroe Bank Channel
│   ├── fw2015.py            # Frajka-Williams 2015 dataset (26°N)
│   ├── arcticgateway.py     # Arctic Gateway transports
│   ├── calafat2025.py       # Calafat 2025 heat transport
│   ├── zheng2024.py         # Zheng 2024 freshwater transport
│   ├── noac47n.py           # NOAC monitoring (47°N)
│   ├── sf2021.py            # MOC from satellite altimetry (26°N)
│   ├── nac.py               # North Atlantic Current transport
│   ├── lebras35n.py         # MOC from moorings, floats and satellite observations (35°N)
│   ├── axmoc34s.py          # MOC, MHT and FOV (34.5°S)
│   └── axmoc22s.py          # MOC and MHT (22.5°S)
│
├── metadata/                # YAML metadata files for standardization
├── standardise.py           # Data standardization functions
├── contributors.py          # Contributor/institution standardization & consolidation
├── convert.py               # Conversion to the AC1 output format
├── compliance_checker.py    # AC1 format compliance checking
├── defaults.py              # Default configs & canonical metadata attribute order
├── utilities.py             # Core utilities (downloads, parsing, validation)
├── logger.py                # Structured logging system
├── plotters.py              # Visualization and plotting functions
├── tools.py                 # Analysis and calculation functions
├── writers.py               # Data export functionality
└── report.py                # Per-dataset report generator

tests/                       # Unit tests (repo root, not inside the package)
```

## Development

### Running Tests
All new functions should include tests. You can run tests locally and generate a coverage report with:
```bash
pytest --cov=amocatlas --cov-report term-missing tests/
```

Try to ensure that all the lines of your contribution are covered in the tests.

### Generating Dataset Reports
AMOCatlas includes automated report generation for dataset documentation:

```bash
# Generate reports for all supported arrays
python generate_report

# Generate report for a specific dataset
python generate_report --data_source rapid

# Generate reports with custom output directory
python generate_report --output_dir custom_reports/
```

Reports are generated as structured RST files in `docs/source/reports/` with:
- Dataset visualization plots
- Variable mapping tables (original → standardized names)
- Metadata documentation
- Temporal coverage analysis
- Statistical summaries

### Code Quality
```bash
ruff format amocatlas/ tests/     # Format code
ruff check amocatlas/ tests/     # Lint code
```

### Working with Notebooks
You can run the example jupyter notebook by launching jupyterlab with `jupyter-lab` and navigating to the `notebooks` directory, or in VS Code or another python GUI.

### Documentation
To build the documentation locally you need to install a few extra requirements:

- Install `make` for your computer, e.g. on ubuntu with `sudo apt install make`
- Install `pandoc` (nbsphinx renders the notebooks through it), e.g. on ubuntu with `sudo apt install pandoc`, or from conda-forge
- Install the documentation extras. Activate the environment you use for working with amocatlas, navigate to the top directory of this repo, then run `pip install -e ".[docs]"`

Once you have the extras installed, you can build the docs locally by navigating to the `docs/` directory and running `make clean html`. This command will create a directory called `build/` which contains the html files of the documentation. Open the file `docs/build/html/index.html` in your browser, and you will see the docs with your changes applied.

## Funding & Support

<div align="center">
  <img src="docs/source/_static/epoc-logo.jpg" alt="EPOC Logo" width="300"/>
</div>

This project is supported by the Horizon Europe project **EPOC - Explaining and Predicting the Ocean Conveyor** (Grant Agreement No. 101081012).

*Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.*


## Acknowledgements

The observing arrays and datasets accessed through AMOCatlas are supported by:

- **RAPID data**: Data from the RAPID-MOCHA-WBTS observing project are funded by the Natural Environment Research Council, the National Science Foundation (NSF), with support from NOAA. They are freely available from www.rapid.ac.uk/.

- **MOVE data**: The MOVE project is made possible with funding from the NOAA Climate Program Office under award NA15OAR4320071 and carried out by principal investigators Uwe Send and Matthias Lankhorst. Initial funding came from the German Bundesministerium fuer Bildung und Forschung. MOVE data are made freely available through the international OceanSITES program.

- **OSNAP data**: OSNAP data were collected and made freely available by the OSNAP (Overturning in the Subpolar North Atlantic Program) project and all the national programs that contribute to it (www.o-snap.org).

- **SAMBA data**: SAMBA data were collected and made freely available by the SAMOC international project and contributing national programs


- **41°N data**: These data were collected and made freely available by the International Argo Program and the national programs that contribute to it. The Argo Program is part of the Global Ocean Observing System

- **DSO data**: Generated by Institution of Oceanography Hamburg and Marine and Freshwater Research Institute (Reykjavik, Iceland). Supported through funding from NACLIM (EU-FP7, grant 308299), RACE II, RACE-Synthese (German BMBF), Nordic WOCE, VEINS, MOEN, ASOF-W, NAClim, THOR, AtlantOS, and Blue Action

- **FBC data**: The time series was generated by the Faroe Marine Research Institute, Faroe Islands. Funding for the in situ Faroe Bank Channel measurements is from the Environmental Research Programme of the Nordic Council of Ministers (NMR) 1993–1998, from national Nordic research councils, from the Danish DANCEA programme, and from the European Framework Programs, lately under grant agreement no. 633211 (AtlantOS) and under grant agreement no. 101136548 (ObsSea4Clim).

- **Arctic Gateway data**: This work is funded by the European Union as part of the EPOC project (Explaining and Predicting the Ocean Conveyor; grant number: 101059547). Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.

- **CALAFAT2025 data**: This work has been carried out within the framework of the EPOC project funded by the European Union's Horizon Europe programme (grant agreement No 101059547), under call HORIZON-CL6-2021-CLIMATE01. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.

- **FW2015 data**: Based on Frajka-Williams, E. (2015), "Estimating the Atlantic overturning at 26°N using satellite altimetry and cable measurements"

- **SF2021 data**: The authors thank the reviewers for their helpful comments. The authors also thank the many officers, crew, and technicians who helped to collect these data. Alejandra Sanchez-Franks also thanks Louis Clément for helpful discussions on normal-mode decomposition. This research has been supported by grants from the UK Natural Environment Research Council for the RAPID-AMOC programme and the ACSIS programme (grant no. NE/N018044/1) as well as funding from the European Union Horizon 2020 Research and Innovation programme BLUE-ACTION (grant no. 727852).

- **NAC data**: Earlier versions of this dataset were created with support from the European Commission through awards EVK2-CT-2000-00087 and EVR1-CT-2001-40014 (projects 'GYROSCOPE' and 'ANIMATE'). Updated versions were partially supported through award NA15OAR4320071 from U.S. NOAA OOMD.

- **Le Bras 35°N data**: ILB and JW gratefully acknowledge the National Aeronautics and Space Administration Grant 80NSSC20K0421. This work was done in part at the Jet Propulsion Laboratory, California Institute of Technology under a contract from NASA. The Argo float data were collected and made freely available by the International Argo Program and the national programs that contribute to it (https://argo.ucsd.edu,https://www.ocean-ops.org). The Argo Program is part of the Global Ocean Observing System. ECCO is supported by NASA's Physical Oceanography, Modeling Analysis and Prediction, and Cryosphere programs. We thank John Toole, Magdalena Andres, and the many other scientists and mariners who went to sea to collect the in situ observational data, particularly through the Line W program.

- **AXMOC 22.5°S data**: This research was carried out in part under the auspices of the Cooperative Institute for Marine and Atmospheric Studies, a cooperative institute of the University of Miami and the National Oceanic and Atmospheric Administration (NOAA), cooperative agreement NA20OAR4320472, and was supported by NOAA's Atlantic Oceanographic and Meteorological Laboratory (AOML). MG and DLV were also supported by the National Oceanic and Atmospheric Administration (NOAA) Climate Variability and Predictability program (Grant NA20OAR4310407).

- **AXMOC 34.5°S data**: The author(s) declare that financial support was received for the research, authorship, and/or publication of this article. This research was carried out in part under the auspices of the Cooperative Institute for Marine and Atmospheric Studies, a cooperative institute of the University of Miami and the National Oceanic and Atmospheric Administration (NOAA), cooperative agreement NA20OAR4320472, and was supported by NOAA's Atlantic Oceanographic and Meteorological Laboratory (AOML). MG and DLV were also supported by the National Oceanic and Atmospheric Administration (NOAA) Climate Variability and Predictability program (Grant NA20OAR4310407)

Dataset access and processing via [AMOCatlas](https://github.com/AMOCcommunity/AMOCatlas).

## Contributing

All contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## PyGMT add-on

AMOCatlas includes support for creating publication-quality figures using PyGMT. The demo notebook `notebooks/amoc_paperfigs.ipynb` demonstrates how to generate figures similar to those in Frajka-Williams et al. (2019, 2023) papers, including filtered time series, component breakdowns, and multi-array comparisons.

**Note**: PyGMT can be challenging to install due to its dependency on GMT. See the [PyGMT installation guide](https://www.pygmt.org/latest/install.html) for platform-specific instructions. PyGMT is an optional dependency - all other AMOCatlas functionality works without it.

Example figures generated by the notebook:

**Multi-array AMOC comparison:**
<img src="docs/source/_static/paperfigs/amoc_multi_array.png" alt="Atlantic Meridional Overturning Circulation time series from four major observing arrays: OSNAP at subpolar latitudes (green), RAPID at 26°N (red), MOVE at 16°N (magenta), and SAMBA at 34.5°S (blue anomaly). Data spans 2000-2025 showing AMOC transport in Sverdrups and variability across different latitudes." width="600"/>

**Multi-array AMOC comparison (filtered):**
<img src="docs/source/_static/paperfigs/amoc_multi_array_filtered.png" alt="Low-pass filtered Atlantic Meridional Overturning Circulation time series using Tukey window filtering to highlight long-term trends. Shows OSNAP, RAPID, MOVE, and SAMBA MOC transport data with reduced high-frequency variability, revealing decadal-scale changes in ocean circulation strength from 2000-2025." width="600"/>

**Historical AMOC (Bryden 2005):**
<img src="docs/source/_static/paperfigs/bryden2005_amoc.png" alt="Historical Atlantic Meridional Overturning Circulation estimates from Bryden et al. 2005 showing AMOC decline from 1957 to 2004. Red line and diamond markers indicate MOC transport measurements at 26°N, demonstrating significant weakening of Atlantic overturning circulation over five decades from 23 to 15 Sverdrups." width="400"/>

---

*For questions or support, please open an [issue](https://github.com/AMOCcommunity/amocatlas/issues) or check our [documentation](https://amoccommunity.github.io/AMOCatlas/).*