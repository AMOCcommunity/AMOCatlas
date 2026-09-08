#!/usr/bin/env python3
"""Script to alphabetize the contributor registry by last name.

This script reads the contributor_registry.yml file, sorts all contributors
alphabetically by their last name (extracted from standard_name), and
rewrites the file with the sorted order while preserving all other content.
"""

import re
from collections import OrderedDict
from pathlib import Path

import yaml


def extract_last_name(standard_name: str) -> str:
    """Extract the last name from a standard name string.

    Simple approach: return the string after the last space.

    Examples
    --------
    - "John Smith" -> "Smith"
    - "M. Femke de Jong" -> "Jong"
    - "Tiago Carrilho Biló" -> "Biló"
    - "L. de Steur" -> "Steur"
    - "Ben I. Moat" -> "Moat"

    """
    # Remove any trailing periods and extra whitespace
    name = standard_name.strip().rstrip(".")

    # Split by spaces and get the last part
    parts = name.split()

    if len(parts) == 0:
        return name

    # Return the last part as the last name
    return parts[-1]


def sort_contributors_by_last_name() -> None:
    """Sort contributors in the registry by last name."""
    # Path to the contributor registry
    registry_file = (
        Path(__file__).parent.parent
        / "amocatlas"
        / "metadata"
        / "contributor_registry.yml"
    )

    # Read the YAML file
    with open(registry_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract contributors section
    contributors = data.get("contributors", {})

    # Create list of (orcid, contributor_data, last_name) tuples
    contributor_list = []

    for orcid, contributor_data in contributors.items():
        standard_name = contributor_data.get("standard_name", "")
        last_name = extract_last_name(standard_name)
        contributor_list.append((orcid, contributor_data, last_name, standard_name))

    # Sort by last name (case-insensitive)
    contributor_list.sort(key=lambda x: x[2].lower())

    # Print the sorting for verification
    print("Sorting contributors by last name:")
    for orcid, _, last_name, standard_name in contributor_list:
        print(f"  {last_name:15} <- {standard_name:25} ({orcid})")

    # Rebuild the contributors dictionary in sorted order
    sorted_contributors = OrderedDict()
    for orcid, contributor_data, _, _ in contributor_list:
        sorted_contributors[orcid] = contributor_data

    # Update the data with sorted contributors
    data["contributors"] = sorted_contributors

    # Read the original file to preserve comments and structure
    with open(registry_file, encoding="utf-8") as f:
        original_content = f.read()

    # Extract header comments (everything before 'contributors:')
    lines = original_content.split("\n")
    header_lines = []

    for line in lines:
        if line.strip().startswith("contributors:"):
            break
        header_lines.append(line)

    # Find the example/footer comments (everything after the last contributor entry)
    footer_lines = []
    in_contributors = False

    for line in lines:
        if line.strip().startswith("contributors:"):
            in_contributors = True
            continue

        if in_contributors:
            # Check if this is a new ORCID entry (starts with quote)
            if re.match(r'^\s*"[0-9-]+.*":\s*', line) or re.match(
                r'^\s*"[a-z-]+-id":\s*', line
            ):
                continue
            # Check if we've hit the example/footer section
            if line.strip().startswith("#") and "example usage" in line.lower():
                # Found the footer, collect remaining lines
                footer_lines = lines[lines.index(line) :]
                break

    # Write the file back with sorted contributors
    with open(registry_file, "w", encoding="utf-8") as f:
        # Write header
        f.write("\n".join(header_lines) + "\n")
        f.write("\ncontributors:\n")

        # Write sorted contributors
        for orcid, contributor_data in sorted_contributors.items():
            f.write(f'  "{orcid}":\n')
            f.write(f'    standard_name: "{contributor_data["standard_name"]}"\n')
            f.write("    name_variants:\n")
            for variant in contributor_data.get("name_variants", []):
                f.write(f'      - "{variant}"\n')
            f.write(f'    id_url: "{contributor_data.get("id_url", "")}"\n\n')

        # Write footer if it exists
        if footer_lines:
            f.write("\n".join(footer_lines))
        else:
            # Add basic example usage
            f.write("# Example usage:\n")
            f.write(
                '# 1. During standardization, extract raw contributor name: "B. Moat"\n'
            )
            f.write("# 2. Search all name_variants across ORCIDs to find match\n")
            f.write("# 3. Use ORCID key to populate:\n")
            f.write('#    - contributor_id: "0000-0002-3644-8181"\n')
            f.write('#    - contributor_name: "Ben I. Moat" (standardized)\n')

    print(
        f"\nSuccessfully sorted {len(contributor_list)} contributors and updated {registry_file}"
    )


if __name__ == "__main__":
    sort_contributors_by_last_name()
