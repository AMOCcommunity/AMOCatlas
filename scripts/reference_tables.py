#!/usr/bin/env python3
"""Generate comprehensive variable reference documentation automatically.

This script generates documentation tables from standardized datasets showing:
- Variable name mappings (original → standardized) across all datasets
- Standard names, long names, and units for each variable


The documentation is generated automatically from the actual standardized datasets
to ensure accuracy and consistency. This script leverages the existing report.py
infrastructure to avoid code duplication.
"""

import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add amocatlas to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import amocatlas.read as read
from amocatlas.defaults import ARRAY_NAMES

# Configure logging to suppress info messages
logging.getLogger("amocatlas").setLevel(logging.WARNING)


def load_all_datasets() -> dict[str, list]:
    """Load all available datasets using the read API with all_files=True."""
    datasets = {}

    # Use centralized array names from defaults.py
    array_names = ARRAY_NAMES

    for array_name in array_names:
        try:
            # Special case: only load first file for arcticgateway to avoid repetition
            if array_name == "arcticgateway":
                print(f"Loading {array_name} (single file)...")
                reader_func = getattr(read, array_name)
                single_dataset = reader_func()  # Just one file
                datasets[array_name] = [single_dataset]  # Wrap in list for consistency
            else:
                print(f"Loading {array_name} (all files)...")
                # Use the read API to load all datasets for comprehensive mapping coverage
                reader_func = getattr(read, array_name)
                all_datasets = reader_func(all_files=True)
                # Store all datasets for this array
                datasets[array_name] = all_datasets

        except (AttributeError, ValueError, KeyError, OSError, TypeError) as e:
            print(f"Warning: Could not load {array_name}: {e}")

    return datasets


def extract_variable_mappings(datasets: dict[str, list]) -> dict[str, dict[str, Any]]:
    """Extract variable mapping information from datasets."""
    all_mappings = {}

    for array_name, dataset_list in datasets.items():
        # Handle the fact that each array now returns a list of datasets
        for i, dataset in enumerate(dataset_list):
            attrs = dataset.attrs

            # Extract metadata for variable mappings
            variable_mapping = attrs.get("variable_mapping", {})
            applied_mapping = attrs.get("applied_variable_mapping", {})
            original_metadata = attrs.get("original_variable_metadata", {})
            source_file = attrs.get("source_file", "Unknown")

            # Create a unique key for each file within an array
            file_key = f"{array_name}_{i}" if len(dataset_list) > 1 else array_name

            # Store mapping info
            all_mappings[file_key] = {
                "array_name": array_name,
                "variable_mapping": variable_mapping,
                "applied_mapping": applied_mapping,
                "original_metadata": original_metadata,
                "source_file": source_file,
                # "dataset_vars": {var: dataset[var] for var in dataset.data_vars},
            }

    return all_mappings


def extract_standardized_variables(
    datasets: dict[str, list],
) -> dict[str, dict[str, list]]:
    """Extract standardized variable information across all datasets."""
    standardized_vars = defaultdict(lambda: defaultdict(list))

    for array_name, dataset_list in datasets.items():
        # Handle the fact that each array now returns a list of datasets
        for dataset in dataset_list:
            for var_name in dataset.data_vars:
                var = dataset[var_name]

                # Extract variable metadata
                var_info = {
                    "array": array_name,
                    "long_name": var.attrs.get("long_name", ""),
                    "description": var.attrs.get("description", ""),
                    "units": var.attrs.get("units", ""),
                    "standard_name": var.attrs.get("standard_name", ""),
                    "shape": str(var.shape),
                    "dims": list(var.dims),
                }

                standardized_vars[var_name]["instances"].append(var_info)

    return standardized_vars


def extract_unit_conversions(datasets: dict[str, list]) -> dict[str, Any]:
    """Extract unit conversion information from datasets."""
    unit_conversions = {}

    for _array_name, dataset in datasets.items():
        attrs = dataset.attrs

        # Look for unit standardization info in processing history
        _history = attrs.get("history", "")
        _processing_notes = attrs.get("processing_notes", "")

        # Extract any unit conversion information
        # TODO This would need to be enhanced based on how unit conversions are logged

    return unit_conversions


def generate_variable_mapping_table(mappings: dict[str, dict[str, Any]]) -> list[str]:
    """Generate RST table showing variable mappings across datasets."""
    rst_content = []

    rst_content.extend(
        [
            "Variable Summary (auto-generated)",
            "======================================",
            "",
            "This table shows how original variable names from each dataset are mapped to standardized names.",
            "",
        ]
    )

    # Collect all mappings for both tables
    all_mappings = []

    for _file_key, info in mappings.items():
        array_name = info["array_name"]
        source_file = info["source_file"]
        # Extract filename after last "/"
        filename = source_file.split("/")[-1] if "/" in source_file else source_file

        # Add hyphenation hints for long filenames to help with table formatting
        # Target length: same as "OS_MOVE_20000206-20221014_DPR_VOLUMETRANSPORT.nc" (45 characters)
        if len(filename) > 45:
            # Add strategic hyphens for common long patterns
            if "VOLUMETRANSPORT" in filename:
                filename = filename.replace("VOLUMETRANSPORT", "VOLUME-TRANSPORT")
            elif "TEMPERATURE-SALINITY" in filename:
                filename = filename.replace("TEMPERATURE-SALINITY", "TEMP-SALINITY")
            elif "CURRENTS-AT-SITES" in filename:
                filename = filename.replace(
                    "CURRENTS-AT-SITES", "CURRENTS-AT-SITES"
                )  # Already has hyphens
            elif "TimeSeries" in filename:
                filename = filename.replace("TimeSeries", "Time-Series")
            elif "Streamfunction" in filename:
                filename = filename.replace("Streamfunction", "Stream-function")

        dataset_file = f"{array_name.upper()} {filename}"

        if info["variable_mapping"]:
            for orig_name, std_name in info["variable_mapping"].items():
                # Apply hyphenation to long variable names (especially SAMBA)
                display_orig_name = orig_name
                if len(orig_name) > 45:  # Same threshold as filenames
                    # Replace underscores with hyphens for better line breaking
                    display_orig_name = orig_name.replace("_", "-")

                all_mappings.append(
                    {
                        "dataset_file": dataset_file,
                        "original_name": display_orig_name,
                        "standardized_name": std_name,
                    }
                )
        else:
            all_mappings.append(
                {
                    "dataset_file": dataset_file,
                    "original_name": "*No mappings*",
                    "standardized_name": "*No mappings*",
                }
            )

    # First table: sorted by dataset
    rst_content.extend(
        [
            ".. tabularcolumns:: |p{2.5cm}|p{3cm}|L|",
            "",
            ".. list-table:: Variable Name Mappings by Dataset",
            "   :header-rows: 1",
            "   :widths: 40 30 30",
            "",
            "   * - Dataset & File",
            "     - Original Name",
            "     - Standardized Name",
        ]
    )

    for mapping in all_mappings:
        rst_content.append(f"   * - **{mapping['dataset_file']}**")
        rst_content.append(f"     - ``{mapping['original_name']}``")
        rst_content.append(f"     - ``{mapping['standardized_name']}``")

    rst_content.extend(["", ""])

    # Second table: sorted by standardized name
    rst_content.extend(
        [
            "Variable Name Mappings by Standardized Name",
            "===========================================",
            "",
            "The same mappings sorted by standardized variable name for easy lookup.",
            "",
        ]
    )

    # Sort by standardized name, then by dataset
    sorted_mappings = sorted(
        all_mappings, key=lambda x: (x["standardized_name"], x["dataset_file"])
    )

    rst_content.extend(
        [
            ".. tabularcolumns:: |p{3cm}|p{4cm}|L|",
            "",
            ".. list-table:: Variable Name Mappings by Standardized Name",
            "   :header-rows: 1",
            "   :widths: 30 40 30",
            "",
            "   * - Standardized Name",
            "     - Dataset & File",
            "     - Original Name",
        ]
    )

    for mapping in sorted_mappings:
        rst_content.append(f"   * - ``{mapping['standardized_name']}``")
        rst_content.append(f"     - **{mapping['dataset_file']}**")
        rst_content.append(f"     - ``{mapping['original_name']}``")

    rst_content.extend(["", ""])
    return rst_content


def generate_standardized_variables_table(
    standardized_vars: dict[str, dict[str, list]],
) -> list[str]:
    """Generate RST table showing standardized variable details."""
    rst_content = []

    rst_content.extend(
        [
            "Standardized Variables Reference",
            "================================",
            "",
            "This table shows all standardized variable names used across datasets with their metadata.",
            "",
        ]
    )

    rst_content.extend(
        [
            ".. list-table:: Standardized Variables",
            "   :header-rows: 1",
            "   :widths: 20 20 10 15 15 20",
            "",
            "   * - Variable Name",
            "     - Description/Long Name",
            "     - Units",
            "     - Standard Name",
            "     - Vocabulary",
            "     - Used In Datasets",
        ]
    )

    for var_name in sorted(standardized_vars.keys()):
        instances = standardized_vars[var_name]["instances"]

        # Get the most common/representative metadata
        long_names = [inst["long_name"] for inst in instances if inst["long_name"]]
        descriptions = [
            inst["description"] for inst in instances if inst["description"]
        ]
        units_list = [inst["units"] for inst in instances if inst["units"]]
        standard_names = [
            inst["standard_name"] for inst in instances if inst["standard_name"]
        ]
        arrays = [inst["array"] for inst in instances]

        # Use most common or first available
        long_name = long_names[0] if long_names else ""
        if descriptions and descriptions[0]:
            description = descriptions[0]
        else:
            description = long_name

        units = units_list[0] if units_list else ""
        standard_name = standard_names[0] if standard_names else ""
        array_list = ", ".join(sorted(set(arrays)))

        # Determine vocabulary URL based on standard_name
        vocabulary_url = ""
        if standard_name:
            if any(
                name in standard_name.lower()
                for name in ["ocean_", "sea_water_", "northward_", "transport"]
            ):
                vocabulary_url = "`CF-1.8 <https://cfconventions.org/Data/cf-standard-names/current/>`_"
            elif (
                "Transport_anomaly" in standard_name
                or "Heat_transport" in standard_name
                or "Freshwater_transport" in standard_name
            ):
                vocabulary_url = "AMOCatlas extension"
            else:
                vocabulary_url = "`CF-1.8 <https://cfconventions.org/Data/cf-standard-names/current/>`_"

        rst_content.append(f"   * - ``{var_name}``")
        rst_content.append(f"     - {description}")
        rst_content.append(f"     - {units}")
        rst_content.append(f"     - {standard_name}")
        rst_content.append(f"     - {vocabulary_url}")
        rst_content.append(f"     - {array_list}")

    rst_content.extend(["", ""])
    return rst_content


def generate_full_reference_documentation(datasets: dict[str, list]) -> str:
    """Generate complete reference documentation."""
    print("Extracting variable mappings...")
    mappings = extract_variable_mappings(datasets)

    print("Extracting standardized variables...")
    standardized_vars = extract_standardized_variables(datasets)

    # Generate all sections
    rst_content = []

    # Header
    rst_content.extend(
        [
            "======================================",
            "Appendix: Actual variables + mappings",
            "=====================================",
            "",
            ".. note::",
            "   This documentation is automatically generated from the standardized datasets",
            "   to ensure accuracy and consistency. Last updated: |today|",
            "",
        ]
    )

    # Add each section
    rst_content.extend(generate_variable_mapping_table(mappings))
    rst_content.extend(generate_standardized_variables_table(standardized_vars))

    return "\n".join(rst_content)


def main() -> None:
    """Generate the variable reference documentation."""
    print("Loading all datasets...")
    datasets = load_all_datasets()
    print(f"Loaded {len(datasets)} datasets")

    print("Generating reference documentation...")
    rst_content = generate_full_reference_documentation(datasets)

    # Write to the correct location in docs tree
    docs_dir = Path(__file__).parent.parent / "docs" / "source" / "reference"
    output_file = docs_dir / "variables.rst"

    # Ensure docs directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(rst_content)
    print(f"Documentation written to {output_file}")


if __name__ == "__main__":
    main()
