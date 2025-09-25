# Project Coding Conventions

This document captures the coding conventions used consistently across the project. It serves as a style guide for future development, keeping the codebase clean, maintainable, and predictable.

---

## Python Style

### Function Definitions
- **Type-Annotated Signatures**: Functions are written with explicit type hints for all parameters and return types.
  ```python
  def load_dataset(
      array_name: str,
      source: str = None,
      file_list: str | list[str] = None,
      transport_only: bool = True,
      data_dir: str | Path | None = None,
      redownload: bool = False,
  ) -> list[xr.Dataset]:
  ```
- Preferred for all public functions and internal functions that aren't trivial.

### Function Naming
- **Snake case**, all lowercase, words separated by underscores.
  Example: `load_sample_dataset()`, `convert_units_var()`.

### Docstrings
- **NumPy-style docstrings** for all functions.
- Structured sections: `Parameters`, `Returns`, and optional `Notes`.
- Keeps in-project and external documentation tools (like Sphinx) clean and uniform.
- Reference: [NumPy Documentation Style Guide](https://numpydoc.readthedocs.io/en/latest/format.html)

**Example:**
```python
def convert_units_var(
    var_values: xr.DataArray,
    current_unit: str,
    new_unit: str,
    unit_conversion: dict = unit_conversion,
) -> xr.DataArray:
    """
    Convert variable values from one unit to another.

    Parameters
    ----------
    var_values : xr.DataArray
        The numerical values to convert.
    current_unit : str
        Unit of the original values.
    new_unit : str
        Desired unit for the output values.
    unit_conversion : dict, optional
        Dictionary containing conversion factors between units.

    Returns
    -------
    xr.DataArray
        Converted values in the desired unit.

    Notes
    -----
    If no valid conversion is found, the original values are returned unchanged.
    """
    ...
```
- The dashes under section headers (e.g., `----------`) are part of the style.
- Optional sections include `Examples`, `See Also`, and `References`.

### Line Length
- **88 characters** line length, following Black defaults.
- Line breaks follow Black's opinionated style: when breaking arguments, use vertical alignment (one per line).
- Reference: [Black: The Uncompromising Code Formatter](https://black.readthedocs.io/en/stable/)

### Code Formatter
- **Black** is used for automatic formatting.
- Pre-commit hooks enforce formatting on commit.

### Imports
- **Ruff** is used for import sorting and linting.
- Imports are automatically ordered and cleaned, with standard library imports first, followed by third-party libraries, and then local imports.
- Reference: [Ruff Documentation](https://docs.astral.sh/ruff/)

---

## Xarray Dataset Style

### Variables, Dimensions, Coordinates
- **ALL CAPITALS** for clarity and consistency.
- Example: `TRANSPORT`, `DEPTH`, `LATITUDE`, `TIME`.

### Attributes
- Follow the [OceanGlidersCommunity OG1 Format](https://oceangliderscommunity.github.io/OG-format-user-manual/OG_Format.html).
- Use **lowercase with underscores** or **camelCase**, depending on context (OG1 style guide is mixed).
- Avoid all capitals and avoid spaces.

### Notes
- Avoid including units in variable names; units are handled via attributes.
- Variables (with the exception of time) should have the `units` attribute.
- Consistent units and metadata are enforced through helper functions and utilities.

---

## Miscellaneous

### Pre-commit Workflow
- Pre-commit hooks are used for Black formatting, Ruff linting, and pytest.
- Ruff handles both import sorting and code linting.
- Pytest is configured to run only when files in `amocatlas/`, `notebooks/`, or `tests/` are modified.

### Logging
- (Planned) Switch from `print()` to proper `logging` for warnings and information.

### Error Handling
- Current philosophy is to fail clearly or log warnings, especially in utility functions like unit conversion.

---

## Future Considerations

- Add `mypy` for static type checking.
- Expand logging configuration for debug and info levels.
- Consistent metadata handling across all data readers.
- Optional doc generation with Sphinx + Read the Docs.

---

*This document was drafted with the help of ChatGPT, in collaboration with the project developer.*

