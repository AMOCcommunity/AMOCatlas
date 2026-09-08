# Developer Guide for AMOCatlas

This guide covers how to contribute to AMOCatlas: setting up an environment, adding a new
data reader, code standards, and testing.

**Contents:**
- [Quickstart](#quickstart)
- [Project overview](#project-overview)
- [Development environment](#development-environment)
- [Adding a new data reader](#adding-a-new-data-reader)
- [Code standards](#code-standards)
- [Testing](#testing)
- [Git workflow](#git-workflow)

For a step-by-step Git walkthrough see {doc}`git_beginners_guide`; for CI/CD and releases see
{doc}`actions`; for maintenance tasks see {doc}`housekeeping`.

---

## Quickstart

```bash
# 1. Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/amocatlas.git
cd amocatlas

# 2. Set up a development environment
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# 3. Branch, change, test
git switch -c yourname-feature
pytest -m "not slow"
ruff check . && ruff format .

# 4. Commit and push, then open a PR on GitHub
git commit -am "feat: describe your change"
git push origin yourname-feature
```

---

## Project overview

AMOCatlas provides unified access to data from AMOC observing arrays and related estimates,
standardising variable names, units, and metadata across sources. It creates no new science
data: it re-serves the values published by each source with consistent formatting and
provenance.

### Core architecture

```
amocatlas/
├── read.py              # Recommended API — read.rapid(), read.osnap(), ...
├── readers.py           # Legacy API — load_dataset(), load_sample_dataset()
├── reader_utils.py      # Shared helpers for the individual readers
├── data_sources/        # One module per array/product (rapid26n.py, osnap55n.py, ...)
├── metadata/            # Per-array YAML metadata + array_schema.json
├── standardise.py       # Naming, units, and metadata standardisation
├── contributors.py      # Contributor / institution consolidation
├── convert.py           # Conversion to the AC1 output format
├── compliance_checker.py# AC1 format compliance checks
├── defaults.py          # Default configs and canonical attribute order
├── utilities.py         # Downloads, parsing, validation
├── plotters.py          # Visualisation (matplotlib + optional PyGMT)
├── tools.py             # Analysis / calculation functions
├── writers.py           # Data export
├── report.py            # Per-dataset report generator
└── logger.py            # Structured logging
```

**Data flow:** `read.rapid()` (or the legacy `readers.load_dataset("rapid")`) resolves the array
name through `_get_reader()` in `readers.py`, which calls the matching `read_<array>()` function in
`data_sources/`. That reader downloads and caches the source files, standardises them, and returns
one or more `xarray.Dataset` objects.

### Package-level imports

`amocatlas/__init__.py` imports the submodules (`readers`, `plotters`, `compliance_checker`,
`convert`, ...) so that `from amocatlas import compliance_checker` works and attributes like
`plotters.HAS_PYGMT` are reachable without importing each module by its full path.

---

## Development environment

**Prerequisites:** Python ≥ 3.10, Git, and (optional) PyGMT for publication figures.

```bash
git clone https://github.com/AMOCcommunity/amocatlas.git
cd amocatlas
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"               # editable install, runtime + dev tools
pytest -m "not slow"                  # confirm the setup
```

**Tooling:** Ruff (linting, import order, and formatting; 88-char lines), pytest (tests +
coverage), Sphinx (docs).

**PyGMT** is optional and can be awkward to install; prefer conda-forge
(`conda install pygmt -c conda-forge`) or see the
[PyGMT install guide](https://www.pygmt.org/latest/install.html). All non-PyGMT functionality
works without it.

---

## Adding a new data reader

This is the most common contribution. To add an array called `newarray`:

1. **Create the reader** `amocatlas/data_sources/newarray.py` with a `read_newarray()` function
   that returns a list of standardised datasets:

   ```python
   """Reader for NEWARRAY data."""

   import xarray as xr
   from amocatlas.logger import log_info


   def read_newarray(source: str | None = None, **kwargs) -> list[xr.Dataset]:
       """Read NEWARRAY data and return standardised datasets."""
       log_info("Loading NEWARRAY data...")
       # download, parse, standardise
       return [dataset]
   ```

2. **Export it** from `amocatlas/data_sources/__init__.py` (add the import and list it in
   `__all__`).

3. **Expose the modern API** in `amocatlas/read.py`: import `read_newarray` from `.data_sources`,
   add a `read.newarray()` wrapper following the existing readers, and add `"newarray"` to
   `__all__`. (The legacy `readers.load_dataset` API is deprecated; new arrays are exposed only
   through `read.*`.)

4. **Add metadata** at `amocatlas/metadata/newarray.yml` (title, contributors, institutions,
   licence, citation) so the dataset is enriched and passes the schema in
   `metadata/array_schema.json`.

5. **Add tests** in `tests/` (fast, mocked tests plus an optional `@pytest.mark.slow` integration
   test).

### Adding visualisation functions

Add plotting functions to `amocatlas/plotters.py`. PyGMT functions must call `_check_pygmt()` for a
graceful fallback when PyGMT is absent, return a `pygmt.Figure`, and stamp the figure with
`_add_amocatlas_timestamp(fig)`.

---

## Code standards

- **Type hints** on all public function parameters and return values.
- **NumPy-style docstrings** on all public functions (Parameters, Returns, and Raises where
  relevant).
- **Naming:** `snake_case` for functions/variables; `ALL_CAPS` for xarray data variables
  (e.g. `MOC`, `TRANS`, `MHT`, `TIME`).
- **Line length** 88; imports ordered by Ruff.
- **Units** always live in variable attributes, never in variable names. Use the full word
  `Sverdrup` (not `Sv`, which collides with sieverts).
- **Attributes** are `lowercase_with_underscores`, following OceanSITES conventions, with a few
  variable-attribute additions adopted from OceanGliders OG1 where they do not conflict with
  OceanSITES.

Run before committing:

```bash
ruff format amocatlas/ tests/
ruff check amocatlas/ tests/
pytest -m "not slow" --cov=amocatlas
```

---

## Testing

```bash
pytest -m "not slow"                              # fast tests (CI set)
pytest                                            # all tests, incl. slow integration
pytest --cov=amocatlas --cov-report term-missing  # coverage
pytest tests/test_readers.py::test_load_sample_dataset_rapid  # a single test
```

Place tests in `tests/` named `test_*.py`. Fast, mocked tests run in CI; mark network/integration
tests with `@pytest.mark.slow` (excluded from CI, expected before a PR). Use sample datasets for
fast tests:

```python
from amocatlas import readers


def test_load_sample_dataset():
    ds = readers.load_sample_dataset("rapid")  # raw sample, original variable names
    assert ds is not None
    assert "time" in ds.variables
```

CI runs the fast tests on Windows, macOS, and Linux across supported Python versions on pull
requests and pushes to `main`; see the Actions tab for results.

---

## Git workflow

Full step-by-step instructions (with screenshots) are in {doc}`git_beginners_guide`. In short:

```bash
# One-time: point at the upstream repo
git remote add upstream https://github.com/AMOCcommunity/amocatlas.git

# Keep your fork current
git switch main && git fetch upstream && git merge upstream/main && git push origin main

# Work on a branch, never on main
git switch -c fix-osnap-metadata
```

Use [conventional commit](https://www.conventionalcommits.org/) prefixes in commit messages:
`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`. Push your branch and open a PR
targeting `AMOCcommunity/amocatlas:main`; address review feedback, then merge once approved.

---

## Resources

- [Documentation](https://amoccommunity.github.io/amocatlas/)
- [GitHub repository](https://github.com/AMOCcommunity/amocatlas)
- [Issue tracker](https://github.com/AMOCcommunity/amocatlas/issues)
