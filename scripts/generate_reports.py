#!/usr/bin/env python3
"""Generate dataset reports for Sphinx documentation.

Usage (run from the repo root, with the package installed via `pip install -e .`):
    python scripts/generate_reports.py                      # generates all reports (default)
    python scripts/generate_reports.py --data_source rapid  # generates only RAPID report
    python scripts/generate_reports.py --data_source osnap  # generates only OSNAP report
    etc.
"""

import argparse
from pathlib import Path

from amocatlas.defaults import ARRAY_NAMES

# amocatlas must be importable — install the package in editable mode (`pip install -e .`).
from amocatlas.report import ReportUtils

# Available data sources (centralized in defaults.py)
AVAILABLE_SOURCES = ARRAY_NAMES

ALL_SOURCES = AVAILABLE_SOURCES + ["all"]


def main() -> int:
    """Generate dataset report and save to docs directory."""
    parser = argparse.ArgumentParser(
        description="Generate dataset reports for AMOCatlas documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available data sources:
{", ".join(AVAILABLE_SOURCES)}

Examples:
  python scripts/generate_reports.py                      # generates all reports (default)
  python scripts/generate_reports.py --data_source rapid  # generates only RAPID report
  python scripts/generate_reports.py --data_source osnap  # generates only OSNAP report
        """,
    )
    parser.add_argument(
        "--data_source",
        default="all",
        choices=ALL_SOURCES,
        help="Data source to generate report for (default: 'all' to generate all reports)",
    )
    parser.add_argument(
        "--output_dir",
        default="docs/source/reports",
        help="Output directory for the report (default: docs/source/reports)",
    )

    args = parser.parse_args()

    # Determine which data sources to process
    if args.data_source == "all":
        sources_to_process = AVAILABLE_SOURCES
        print(f"Generating reports for ALL {len(sources_to_process)} data sources...")
    else:
        sources_to_process = [args.data_source]
        print(f"Generating {args.data_source.upper()} array report...")

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each data source
    total_generated = 0
    errors = []

    for source in sources_to_process:
        print(f"\n--- Processing {source.upper()} ---")

        # Generate the report content using the ReportUtils method
        try:
            content = ReportUtils.generate_array_report(source, canonical_dates=True)
            print(f"Generated report with {len(content)} characters")
        except Exception as e:  # noqa: BLE001 - batch tool: continue past a failing array
            import traceback

            error_msg = f"Error generating {source} report: {e}"
            print(error_msg)
            print("Full traceback:")
            traceback.print_exc()
            errors.append(error_msg)
            continue

        # Write the report
        output_file = output_dir / f"{source}_report.rst"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Report saved to: {output_file}")
            print(f"File size: {output_file.stat().st_size} bytes")
            total_generated += 1
        except Exception as e:  # noqa: BLE001 - batch tool: continue past a failing array
            error_msg = f"Error writing {source} report: {e}"
            print(error_msg)
            errors.append(error_msg)

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Successfully generated {total_generated} report(s)")
    if errors:
        print(f"Encountered {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nTo rebuild documentation, run:")
    print("cd docs && make clean html")

    return 0


if __name__ == "__main__":
    exit(main())
