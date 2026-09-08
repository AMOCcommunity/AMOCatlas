# Changelog

All notable changes to AMOCatlas will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New reader for the OVIDE section (`read.ovide()`) (#183)
- New reader for the SCOTIA overturning array (`read.scotia()`) — the first array served in neutral-density (GAMMA) space (#184)
- `amocvocab`, a controlled variable vocabulary under `amocatlas/vocabulary/` (short name → `standard_name`-or-null → units → P02/P01 URI → definition), with a JSON schema and a validator (`validate_amocvocab.py`) that checks every CF `standard_name` against the live CF standard-name table and every unit under UDUNITS; a repo-tracked staging draft (`amocvocab_draft.yml`) is included but not shipped in the wheel (#181)
- New optional metadata field `report_plot_variable` to select the headline variable a per-array report plots (#184)

### Changed
- README rewritten for a first-time scientific reader (#179)
- Standardised output now follows the `amocvocab` + OceanSITES convention (see Breaking changes) (#181)
- Per-array reports regenerated with corrected variable names, and the two report generators consolidated into `scripts/generate_reports.py` (#182)
- Linting is now ruff-only: `ruff format` replaces black, and the pre-commit/codespell configuration was removed (#182)
- Documentation autodoc deduplicated (`amocatlas.rst` reduced to an index; docs build warnings cut from ~140 to 4); the legacy `readers` string API was dropped from the API docs, though the code remains (still deprecated) (#182)
- Dependencies are declared in `pyproject.toml` (`[project] dependencies`, extras `test`/`docs`/`dev`); `requirements.txt`, `requirements-dev.txt` and `environment.yml` removed; install with `pip install -e ".[dev]"`. Docs CI no longer uses conda. A coverage floor of 55% is enforced in CI (#185)

### Fixed
- Report generation now writes plots into the docs tree (`docs/source/_static/reports`) resolved from the project root, instead of creating a stray `docs/source/_static/reports` directory under whatever directory it was invoked from
- Every CF `standard_name` used in array metadata verified against the live CF standard-name table; three fabricated names removed; the transport unit canonicalised to lowercase `sverdrup` (#180)
- Zenodo concept DOI added to the CITATION file and as a README badge (#178)

### Removed
- `writers.save_AC1_dataset()` and its tests, and the AC1 format reference pages (`docs/source/reference/AC1_*.rst`) (#182)

### Breaking changes

- **#182 — AC1 writer and format docs removed.** `writers.save_AC1_dataset()` no longer exists; the only public writer is `writers.save_dataset(ds, output_file)`. Code that imported or called `save_AC1_dataset` must switch to `save_dataset`. The AC1 format reference pages were deleted.
- **#181 — standardised output moved to the `amocvocab` + OceanSITES convention.** A script written against 0.4.0 output must update on two fronts:
  - **Variable names.** OSNAP streamfunctions `STREAMFUNCTION_SIGMA0` / `STREAMFUNCTION_SIGMA0_WEST` / `STREAMFUNCTION_SIGMA0_EAST` are now `PSI_SIGMA0` / `PSI_SIGMA0_WEST` / `PSI_SIGMA0_EAST`; streamfunctions generally standardise to `PSI_Z` / `PSI_SIGMA0` / `PSI_SIGMA2`. SAMBA is reworked to anomalies: `UPPER_TRANSPORT` / `ABYSSAL_TRANSPORT` became `TRANS_UPPER` / `TRANS_ABYSSAL`, and the MOC decomposition is now `MOC_ANOM`, `TRANS_RELATIVE`, `TRANS_REFERENCE`, `TRANS_EKMAN` (with `_WEST` / `_EAST` constituents).
  - **Attributes.** `long_name` values were rewritten to descriptive lowercase and the original provider label is preserved under a new `source_long_name` attribute; `cell_methods` was added where a variable is a max/mean over a coordinate; and `standard_name` was dropped from derived or anomaly quantities that have no exact CF name (vocabulary "Case C"). A 0.4.0 script that keys on an old variable name, on `source_long_name` being absent, or on every variable carrying a `standard_name`, must be updated.

## [0.4.0] - 2026-08-13

### Added
- New reader for the AXMOC 22.5°S and 34.5°S arrays (#142)
- Schema validation for array metadata YAML files (`array_schema.json`), enforced in CI (#171)
- Download provenance: each downloaded file now gets a `<name>.provenance.json` sidecar recording the source URL, download time, byte size, SHA-256, and server ETag/Last-Modified, plus a `read_provenance()` accessor (#175)
- Comprehensive test cases for the FBC (Faroe Bank Channel) and NOAC 47°N readers, and this CHANGELOG

### Changed
- Downloads are now atomic (streamed to a `.part` file and renamed on completion) and use a connect/read timeout, so an interrupted or stalled download can no longer leave a truncated file in the cache (#175)
- Contributor handling: single-contributor datasets are handled correctly and a genuine ORCID is never overwritten by a registry placeholder (#172)
- License metadata normalised toward SPDX identifiers: `fw2015` `CC-BY 4.0` → `CC-BY-4.0`, `mocha26n` `ODC-By` → `ODC-By-1.0`, and `fbc` `CC0-1.0` → `CC-BY-4.0` following the providers' updated Zenodo record
- Documentation deploy runs offline (notebooks are copied, not executed) and `gh-pages` is force-orphaned each deploy to stop history bloat (#174)
- Repository history rewritten to remove large data files committed in the past (fresh-clone size reduced from ~162 MB to ~24 MB)
- Dependency and CI maintenance: bumped xarray, pandas, matplotlib, jinja2, sphinx and other dev/CI dependencies, and added Dependabot (#144–#168)

### Fixed
- TIME coordinate converter now honours the declared epoch and units (e.g. `days since 1950-01-01` decodes to 1950, not 1970); unrecognised units warn instead of silently assuming 1970; and the output `units` attribute is a valid UDUNITS string rather than the numpy dtype name `datetime64[ns]` (#175)
- Internal working structures (`files`, `variable_mapping`, `original_variable_metadata`) are stripped from output attributes so standardised datasets serialise to netCDF without error (#175)
- Metadata conflict resolution corrected, and the metadata drift surfaced by the new schema validation fixed (#171)
- Small metadata updates across several arrays (#143)
- Fixed `__version__` import in `__init__.py` for proper package version access

## [0.3.1] - 2026-06-07

### Added
- New reader for Le Bras AMOC at 35°N (#139)
- New Sanchez-Franks 2021 Reader (#137) 
- New NAC reader (#134)
- Report generation functionality (#140)

### Updated
- Updated FBC transport with new location and extended timeseries (#133)
- Updated metadata for Zheng2024 (#136)
- Updated Zheng2024 plot to 2D (#135)

### Fixed
- Fixed convert lowercase URL into uppercase when case sensitive (#132)
- Fixed standardized sigma coords on RAPID to be <1000 (#126)

## [0.3.0] - 2026-02-10

### Added
- Registry for ORCID/EDMO with contributor alignment and dedupe (#106)
- Report generation of standardised datasets (#105)

### Fixed
- Addressed linting issues (#108)

## [0.2.0] - 2026-02-04

### Added
- New intuitive API (`amocatlas.read` namespace)
- Automatic data standardization
- Enhanced metadata management system
- Comprehensive documentation and reports

### Changed
- Legacy API (`load_dataset`, `load_sample_dataset`) marked as deprecated
- Improved package architecture with modular data sources

## [0.1.1] - 2025-09-26

### Fixed
- Bug fixes and minor improvements

## [0.1.0] - 2025-09-26

### Added
- Initial stable release
- Basic data loading functionality for major AMOC arrays
- Core plotting and analysis tools

## [0.0.4] - 2025-07-06

### Added
- Early development version
- Basic reader implementations

---

### Legend

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

### Release Process

1. Create a new version section above "Unreleased"
2. Move items from "Unreleased" to the new version section
3. Add release date in YYYY-MM-DD format
4. Create git tag with format `v{version}` (e.g., `v0.3.1`)
5. GitHub Actions will automatically publish to PyPI

### Contributing

When adding changes, please:
1. Add new entries under the "Unreleased" section
2. Use the appropriate category (Added, Changed, Fixed, etc.)
3. Include PR numbers in parentheses when applicable
4. Keep descriptions clear and user-focused