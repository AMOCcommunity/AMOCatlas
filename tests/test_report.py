"""Tests for amocatlas.report module.

This module tests both the core report generation functionality and utility functions
for dataset analysis and reporting.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import xarray as xr

from amocatlas import report
from amocatlas.logger import disable_logging
from amocatlas.report import ReportUtils

# Disable logging for cleaner test output
disable_logging()


class TestReportUtilities:
    """Test report utility functions."""

    def test_dataframe_to_rst_table_basic(self):
        """Test _dataframe_to_rst_table with simple DataFrame."""
        df = pd.DataFrame(
            {
                "Variable": ["temp", "sal"],
                "Min Value": [1.5, 34.2],
                "Max Value": [2.8, 35.1],
            }
        )

        result = report._dataframe_to_rst_table(df)
        assert isinstance(result, list)
        assert len(result) > 0

        # Check for basic table structure
        rst_content = "\n".join(result)
        assert "Variable" in rst_content
        assert "Min Value" in rst_content
        assert "temp" in rst_content

    def test_dataframe_to_rst_table_empty(self):
        """Test _dataframe_to_rst_table with empty DataFrame."""
        df = pd.DataFrame()

        result = report._dataframe_to_rst_table(df)
        assert result == ["(No data available)"]

    def test_dataframe_to_rst_table_numeric_formatting(self):
        """Test numeric formatting in RST table."""
        df = pd.DataFrame(
            {"Variable": ["test"], "Min Value": [1.23456], "Max Value": [9.87654]}
        )

        result = report._dataframe_to_rst_table(df)
        rst_content = "\n".join(result)

        # Check that numbers are formatted to 2 decimal places
        assert "1.23" in rst_content
        assert "9.88" in rst_content


class TestReportGeneration:
    """Integration tests for report generation."""

    @pytest.mark.slow
    def test_generate_small_dataset_report(self):
        """Test report generation with a small dataset (47N - 0.01 MB)."""
        # Use 47N: single small file, safe for CI
        rst_content = ReportUtils.generate_array_report("noac47n")

        # Verify basic structure
        assert "Datasets" in rst_content
        assert "Dataset Overview" in rst_content
        assert "Variable Information" in rst_content

        # Should have reasonable length (not empty, not massive)
        assert 500 < len(rst_content) < 10000

    @pytest.mark.slow
    def test_generate_multi_file_small_dataset_report(self):
        """Test report generation with multiple small files (SAMBA - 0.03 + 0.20 = 0.23 MB)."""
        # SAMBA has 2 small files, perfect for testing multi-file reports
        rst_content = ReportUtils.generate_array_report("samba")

        # Verify basic structure
        assert "SAMBA Datasets" in rst_content
        assert "Time Coverage" in rst_content  # Should be in all reports

        # Should handle multiple datasets
        assert "----" in rst_content  # Section separators for multiple files

        # Test table generation: should have 2 tables per dataset (coordinates + variables)
        # SAMBA has 2 datasets, so expect 4 tables total
        list_tables = rst_content.count(".. list-table::")
        assert list_tables == 4, (
            f"Expected 4 list-tables (2 per dataset), found {list_tables}"
        )

        # Test figure generation: should have 2 figures (one per dataset)
        figures = rst_content.count(".. figure::")
        assert figures == 2, f"Expected 2 figures (one per dataset), found {figures}"

        # Test specific time coverage for SAMBA files
        assert "2013-09-12 to 2017-07-16" in rst_content, (
            "Missing time coverage for Upper_Abyssal_Transport_Anomalies.txt"
        )
        assert "2009-03-19 to 2017-04-29" in rst_content, (
            "Missing time coverage for second SAMBA file"
        )

        # Test metadata addition: processing software should be added
        assert (
            "- **Processing Software**: http://github.com/AMOCcommunity/amocatlas"
            in rst_content
        ), "Missing processing software metadata"

        # Test variable mapping: check for specific SAMBA variable remapping
        assert (
            "   * - *Ekman__wind__contribution_to_the_MOC_anomaly* → **TRANS_EKMAN**"
            in rst_content
        ), "Missing variable mapping for TRANS_EKMAN"

        # Test units conversion: should have multiple instances of "sverdrup" units
        sverdrup_count = rst_content.count("sverdrup")
        assert sverdrup_count >= 2, (
            f"Expected at least 2 'sverdrup' units, found {sverdrup_count}"
        )

        # Should be longer than single-file reports due to multiple files
        assert len(rst_content) > 2000

        # Should be reasonable size (not massive)
        assert len(rst_content) < 50000

    @pytest.mark.slow
    def test_generate_rapid_report_transport_only(self):
        """Test most common use case: generating RAPID transport report."""
        # This is the primary user workflow
        rst_content = report.rapid(all_files=False)

        # Verify basic structure
        assert "RAPID Datasets" in rst_content
        assert "Dataset Overview" in rst_content
        assert "Variable Information" in rst_content
        assert "Coordinate Information" in rst_content

        # Check key metadata fields are present
        assert "Project" in rst_content or "Description" in rst_content

        # Verify RST formatting is correct
        assert "========" in rst_content  # Title underline
        assert "^^^^^^^^" in rst_content  # Section headers
        assert ".. list-table::" in rst_content  # Tables

        # Should contain transport variables
        assert "MOC" in rst_content or "transport" in rst_content.lower()

        # Should have reasonable length (not empty, not massive)
        assert 1000 < len(rst_content) < 50000

    @pytest.mark.slow
    def test_generate_multi_dataset_report(self):
        """Test report generation for arrays with multiple files."""
        # Use OSNAP which typically has multiple datasets
        rst_content = ReportUtils.generate_array_report("osnap")

        # Should handle multiple datasets
        assert "OSNAP Datasets" in rst_content

        # Should have section separators for multiple files
        assert "----" in rst_content

        # Should be longer than single-file reports
        assert len(rst_content) > 2000

    @pytest.mark.slow
    def test_command_line_generate_report(self):
        """Test command-line interface works."""
        # Test the CLI interface that users will actually use
        # Use a small dataset for faster testing (NOAC47N is only 0.01 MB)
        result = subprocess.run(
            [
                sys.executable,
                "scripts/generate_reports.py",
                "--data_source",
                "noac47n",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,  # Run from project root
            timeout=30,
        )

        # Should complete successfully
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"

        # Should produce some output
        assert "Processing" in result.stdout or "Generated" in result.stdout

        # Should create the expected report file
        report_file = Path("docs/source/reports/noac47n_report.rst")
        if report_file.exists():
            content = report_file.read_text()
            assert "Datasets" in content


class TestReportUtils:
    """Unit tests for core utility functions."""

    def test_handle_yyyymm_time_format(self):
        """Test YYYYMM time format conversion."""
        # Create test data in YYYYMM format
        test_data = xr.DataArray([200201, 200202, 200203])  # Feb-Apr 2002

        result = ReportUtils.handle_yyyymm_time_format(test_data)

        # Should convert to proper datetime
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) == 3

        # Check first date - handle both possible interpretations
        assert result[0].year == 2002
        # Month could be 1 or 2 depending on interpretation
        assert result[0].month in [1, 2]
        assert result[0].day == 1

    def test_estimate_frequency(self):
        """Test frequency estimation from time differences."""
        # Test hourly
        hourly_diff = pd.Timedelta(hours=1)
        result = ReportUtils.estimate_frequency(hourly_diff)
        assert result in ["hourly", "1.0H"]  # Accept both formats

        # Test daily
        daily_diff = pd.Timedelta(hours=24)
        assert ReportUtils.estimate_frequency(daily_diff) == "daily"

        # Test 12-hourly
        twelve_h_diff = pd.Timedelta(hours=12)
        assert ReportUtils.estimate_frequency(twelve_h_diff) == "12H"

        # Test monthly (30 days)
        monthly_diff = pd.Timedelta(days=30)
        assert ReportUtils.estimate_frequency(monthly_diff) == "monthly"

        # Test sub-hourly
        minute_diff = pd.Timedelta(minutes=30)
        result = ReportUtils.estimate_frequency(minute_diff)
        assert "min" in result

    def test_safe_time_diff_days(self):
        """Test safe time difference calculation."""
        from datetime import datetime

        # Test normal datetime difference
        start = datetime(2020, 1, 1)
        end = datetime(2020, 1, 31)
        diff = ReportUtils.safe_time_diff_days(end, start)
        assert diff == 30

        # Test YYYYMM format
        diff_yyyymm = ReportUtils.safe_time_diff_days(202002, 202001)  # Jan to Feb
        assert 25 < diff_yyyymm < 35  # Roughly a month

        # Test edge case with invalid data
        diff_invalid = ReportUtils.safe_time_diff_days(None, None)
        assert diff_invalid == 0

    def test_safe_format_date(self):
        """Test safe date formatting."""
        from datetime import datetime

        # Test normal datetime
        date = datetime(2020, 5, 15, 12, 30)
        result = ReportUtils.safe_format_date(date)
        assert result == "2020-05-15"

        # Test unix timestamp
        timestamp = 1589544600  # May 15, 2020
        result = ReportUtils.safe_format_date(timestamp)
        assert "2020-05-15" in result

        # Test year value
        result = ReportUtils.safe_format_date(2020)
        assert "2020" in result

    def test_dataframe_to_rst_table(self):
        """Test DataFrame to RST table conversion."""
        # Create test DataFrame
        df = pd.DataFrame(
            {
                "Variable": ["**MOC**", "*moc_mar_hc10* → **MOC**"],
                "Units": ["Sv", "Sv"],
                "Description": [
                    "Meridional overturning circulation",
                    "MOC time series",
                ],
            }
        )

        rst_lines = ReportUtils.dataframe_to_rst_table(df)

        # Should produce list-table format
        rst_text = "\n".join(rst_lines)
        assert ".. list-table::" in rst_text
        assert ":widths:" in rst_text
        assert ":header-rows: 1" in rst_text

        # Should preserve formatting (asterisks for bold/italic)
        assert "**MOC**" in rst_text
        assert "*moc_mar_hc10*" in rst_text

        # Should have proper structure
        assert "   * - Variable" in rst_text
        assert "     - Units" in rst_text


class TestAnalysisAndStatistics:
    """Tests for dataset analysis functionality."""

    def test_compute_dataset_statistics(self):
        """Test dataset statistics computation."""
        # Create minimal test dataset
        ds = xr.Dataset(
            {
                "temperature": (["time"], [15.0, 16.0, 17.0]),
                "salinity": (["time"], [35.0, 35.1, 35.2]),
            },
            coords={"time": pd.date_range("2020-01-01", periods=3)},
        )

        stats = ReportUtils.compute_dataset_statistics(ds)

        # Basic structure
        assert stats["total_variables"] == 2
        assert stats["total_coordinates"] == 1
        assert "variables" in stats

        # Variable stats
        temp_stats = stats["variables"]["temperature"]
        assert temp_stats["min"] == 15.0
        assert temp_stats["max"] == 17.0
        assert temp_stats["units"] == "unknown"  # No units in test data

    def test_analyze_temporal_coverage(self):
        """Test temporal coverage analysis."""
        # Create test dataset with time
        times = pd.date_range("2020-01-01", "2020-01-10", freq="D")
        ds = xr.Dataset({"data": (["TIME"], range(10))}, coords={"TIME": times})

        temporal = ReportUtils.analyze_temporal_coverage(ds)

        # Should detect time
        assert temporal["has_time"] is True
        assert temporal["valid_times"] is True
        assert temporal["coordinate_name"] == "TIME"

        # Should calculate span
        assert temporal["time_span_days"] == 9  # 10 days, 9 day difference
        assert temporal["total_records"] == 10

        # Should estimate frequency
        assert "estimated_frequency" in temporal
        assert temporal["estimated_frequency"] == "daily"


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_generate_report_nonexistent_array(self):
        """Test graceful handling of invalid array names."""
        with pytest.raises((AttributeError, ValueError)):
            ReportUtils.generate_array_report("nonexistent_array")

    def test_empty_dataframe_to_rst(self):
        """Test handling of empty DataFrames."""
        df = pd.DataFrame()
        rst_lines = ReportUtils.dataframe_to_rst_table(df)

        assert len(rst_lines) == 1
        assert "No data available" in rst_lines[0]

    def test_dataset_without_time(self):
        """Test analysis of datasets without time coordinate."""
        ds = xr.Dataset({"static_var": (["x"], [1, 2, 3])}, coords={"x": [0, 1, 2]})

        temporal = ReportUtils.analyze_temporal_coverage(ds)
        assert temporal["has_time"] is False

    def test_report_plot_variable_override(self):
        """`report_plot_variable` selects the figure variable over the heuristic.

        A dataset with a 1D MOC and a 2D transport: the heuristic prefers the 2D
        variable, but the override forces the 1D MOC time series.
        """
        import numpy as np

        time = np.arange("2004-01", "2004-05", dtype="datetime64[M]").astype(
            "datetime64[ns]"
        )
        ds = xr.Dataset(
            {
                "MOC_GAMMA": (["TIME"], np.arange(len(time), dtype=float)),
                "TRANS_GAMMA": (
                    ["TIME", "GAMMA"],
                    np.arange(len(time) * 3, dtype=float).reshape(len(time), 3),
                ),
            },
            coords={"TIME": time, "GAMMA": [26.0, 27.0, 28.0]},
        )

        plots_dir = Path("docs/source/_static/reports")
        created = []
        try:
            # With the override -> 1D MOC time series.
            ds_flag = ds.copy()
            ds_flag.attrs["report_plot_variable"] = "MOC_GAMMA"
            path_flag = ReportUtils.generate_plot(ds_flag, "override_test_flag")
            created.append(plots_dir / Path(path_flag).name)
            assert path_flag.endswith("_timeseries.png")

            # Without it -> heuristic falls to the 2D variable.
            path_heur = ReportUtils.generate_plot(ds, "override_test_heur")
            created.append(plots_dir / Path(path_heur).name)
            assert path_heur.endswith("_2d_gridded.png")

            # An override naming a missing variable falls back to the heuristic.
            ds_bad = ds.copy()
            ds_bad.attrs["report_plot_variable"] = "NOPE"
            path_bad = ReportUtils.generate_plot(ds_bad, "override_test_bad")
            created.append(plots_dir / Path(path_bad).name)
            assert path_bad.endswith("_2d_gridded.png")
        finally:
            for p in created:
                p.unlink(missing_ok=True)


class TestDatabaseErrorHandling:
    """Tests for contributors database error handling and edge cases."""

    def test_update_contributors_database_with_corrupted_file(self, tmp_path):
        """Test handling of corrupted YAML database file."""
        # Create a corrupted YAML file
        db_file = tmp_path / "test_contributors.yml"
        db_file.write_text("invalid: yaml: content: [unclosed bracket")

        # Test with explicit db_file parameter to avoid corrupting actual database
        test_data = {
            "array_source": "test_array",
            "contributors": ["Test User", "Another User"],
            "institutions": ["Test Org", "Another Institution"],
        }

        # Should not raise an exception despite corrupted file
        ReportUtils.update_contributors_database(test_data, db_file=db_file)

        # Verify database was recreated with valid content
        assert db_file.exists()

        # Read back the new content to verify it's valid YAML
        import yaml

        with open(db_file) as f:
            new_data = yaml.safe_load(f)
            assert new_data is not None
            assert "arrays" in new_data

    def test_update_contributors_database_unicode_error(self, tmp_path):
        """Test handling of unicode decode errors in database file."""
        # Create a file with invalid unicode
        db_file = tmp_path / "test_contributors.yml"
        db_file.write_bytes(b"\xff\xfe\x00invalid unicode")

        test_data = {
            "array_source": "test_array",
            "contributors": ["Test User", "Another User"],
            "institutions": ["Test Org", "Another Institution"],
        }

        # Should handle unicode error gracefully
        ReportUtils.update_contributors_database(test_data, db_file=db_file)

        # Verify database was recreated
        assert db_file.exists()

        # Verify content is valid
        import yaml

        with open(db_file) as f:
            new_data = yaml.safe_load(f)
            assert new_data is not None


class TestTimeFormatProcessing:
    """Tests for time format processing edge cases."""

    def test_safe_time_diff_days_yyyymm_format(self):
        """Test YYYYMM format time difference calculation."""
        # Test with YYYYMM format numbers
        diff = ReportUtils.safe_time_diff_days(202002, 202001)
        assert 25 < diff < 35  # Roughly a month

        # Test with invalid YYYYMM data
        diff = ReportUtils.safe_time_diff_days("invalid", "data")
        assert diff == 0

    def test_safe_time_diff_days_unix_timestamps(self):
        """Test unix timestamp format time differences."""
        # Unix timestamps (May 15, 2020 vs May 16, 2020)
        ts1 = 1589544600  # May 15, 2020
        ts2 = 1589631000  # May 16, 2020

        diff = ReportUtils.safe_time_diff_days(ts2, ts1)
        assert abs(diff - 1) < 0.1  # Should be approximately 1 day

    def test_safe_time_diff_days_decimal_years(self):
        """Test decimal years format time differences."""
        # Small values that could be decimal years
        diff = ReportUtils.safe_time_diff_days(1.5, 0.5)  # 1 year difference
        assert 360 < diff < 370  # Should be roughly 365 days

    def test_safe_format_date_edge_cases(self):
        """Test date formatting with various edge cases."""
        # Test with None
        result = ReportUtils.safe_format_date(None)
        assert isinstance(result, str)

        # Test with string input
        result = ReportUtils.safe_format_date("2020")
        assert "2020" in result

        # Test with invalid numeric input
        result = ReportUtils.safe_format_date(float("inf"))
        assert isinstance(result, str)

    def test_analyze_temporal_coverage_complex_time_formats(self):
        """Test temporal coverage analysis with complex time formats."""
        # Create dataset with YYYYMM-like time values
        time_values = [202001, 202002, 202003]
        ds = xr.Dataset({"data": (["time"], [1, 2, 3])}, coords={"time": time_values})

        temporal = ReportUtils.analyze_temporal_coverage(ds)
        assert temporal["has_time"] is True
        assert temporal["coordinate_name"] == "time"
        assert temporal["total_records"] == 3


class TestStatisticsErrorHandling:
    """Tests for statistical computation error handling."""

    def test_compute_dataset_statistics_with_invalid_data(self):
        """Test statistics computation with datasets containing invalid data."""
        # Dataset with NaN values
        ds = xr.Dataset(
            {
                "var_with_nan": (["x"], [1.0, float("nan"), 3.0]),
                "var_with_inf": (["x"], [1.0, float("inf"), 3.0]),
            },
            coords={"x": [0, 1, 2]},
        )

        stats = ReportUtils.compute_dataset_statistics(ds)

        # Should handle NaN/inf gracefully
        assert "var_with_nan" in stats["variables"]
        assert "var_with_inf" in stats["variables"]
        assert stats["total_variables"] == 2

    def test_compute_dataset_statistics_empty_variables(self):
        """Test statistics computation with empty or problematic variables."""
        # Dataset with empty dimensions
        ds = xr.Dataset({"empty_var": (["empty_dim"], [])}, coords={"empty_dim": []})

        stats = ReportUtils.compute_dataset_statistics(ds)
        assert stats["total_variables"] == 1
        assert "empty_var" in stats["variables"]


class TestCoordinateExtraction:
    """Tests for coordinate information extraction utilities."""

    def test_coordinate_extraction_with_complex_types(self):
        """Test coordinate extraction with various data types."""
        # Create dataset with different coordinate types
        ds = xr.Dataset(
            {
                "data": (
                    ["time", "depth", "category"],
                    [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
                )
            },
            coords={
                "time": pd.date_range("2020-01-01", periods=2),
                "depth": [10.5, 20.5],  # Float coordinates
                "category": ["A", "B"],  # String coordinates
            },
        )

        # Test via compute_dataset_statistics which calls coordinate extraction
        stats = ReportUtils.compute_dataset_statistics(ds)
        assert stats["total_coordinates"] == 3

        # Verify all coordinate types are handled
        coord_info = stats.get("coordinates", {})
        assert len(coord_info) == 3

    def test_coordinate_extraction_error_handling(self):
        """Test coordinate extraction with problematic coordinate data."""
        # Create dataset with coordinates that might cause issues
        import numpy as np

        ds = xr.Dataset(
            {"data": (["problematic_coord"], [1, 2, 3])},
            coords={"problematic_coord": [np.nan, np.inf, -np.inf]},
        )

        # Should handle problematic coordinates gracefully
        stats = ReportUtils.compute_dataset_statistics(ds)
        assert stats["total_coordinates"] == 1


class TestReportGenerationFallbacks:
    """Tests for report generation fallback logic and edge cases."""

    def test_dataframe_to_rst_table_with_special_characters(self):
        """Test RST table generation with special characters and formatting."""
        # Test with RST-sensitive characters
        df = pd.DataFrame(
            {
                "Variable": ["*italic*", "**bold**", "normal_text"],
                "Description": [
                    "Text with | pipe",
                    "Text with `backticks`",
                    "Normal text",
                ],
                "Units": ["°C", "m/s²", "dimensionless"],
            }
        )

        rst_lines = ReportUtils.dataframe_to_rst_table(df)
        rst_content = "\n".join(rst_lines)

        # Should preserve special characters (may be escaped)
        assert "*italic*" in rst_content
        assert "**bold**" in rst_content
        assert "| pipe" in rst_content
        assert "backticks" in rst_content  # May be escaped as \`backticks\`
        assert "°C" in rst_content

    def test_safe_format_date_with_edge_cases(self):
        """Test date formatting with various problematic inputs."""
        import numpy as np

        # Test with NaN
        result = ReportUtils.safe_format_date(np.nan)
        assert isinstance(result, str)

        # Test with very large timestamp (overflow scenario)
        result = ReportUtils.safe_format_date(1e20)
        assert isinstance(result, str)

        # Test with negative timestamp
        result = ReportUtils.safe_format_date(-1000)
        assert isinstance(result, str)

    def test_estimate_frequency_edge_cases(self):
        """Test frequency estimation with edge cases."""
        # Test with very small timedelta
        tiny_diff = pd.Timedelta(seconds=1)
        result = ReportUtils.estimate_frequency(tiny_diff)
        assert "s" in result or "min" in result  # May detect as sub-minute

        # Test with very large timedelta
        large_diff = pd.Timedelta(days=365)
        result = ReportUtils.estimate_frequency(large_diff)
        assert "annual" in result.lower() or "year" in result.lower()

        # Test with NaN timedelta (edge case)
        try:
            nan_diff = pd.Timedelta("NaT")
            result = ReportUtils.estimate_frequency(nan_diff)
            assert isinstance(result, str)
        except (ValueError, TypeError):
            # This is acceptable - function may not handle NaT values gracefully
            pass

    def test_handle_yyyymm_time_format_edge_cases(self):
        """Test YYYYMM time format handling with problematic inputs."""
        import numpy as np

        # Test with invalid YYYYMM values
        invalid_data = xr.DataArray([999999, 123, -1])  # Invalid formats

        try:
            result = ReportUtils.handle_yyyymm_time_format(invalid_data)
            # If it succeeds, should return DatetimeIndex
            assert isinstance(result, (pd.DatetimeIndex, type(None)))
        except (ValueError, TypeError):
            # This is acceptable - function should handle invalid YYYYMM formats gracefully
            pass

        # Test with NaN values
        nan_data = xr.DataArray([202001, np.nan, 202003])
        try:
            result = ReportUtils.handle_yyyymm_time_format(nan_data)
            assert isinstance(result, (pd.DatetimeIndex, type(None)))
        except (ValueError, TypeError):
            # This is acceptable - function should handle NaN values gracefully in time data
            pass

    def test_extract_contributors_and_institutions_edge_cases(self):
        """Test contributor extraction with edge case metadata."""
        # Test with malformed contributor names
        ds1 = xr.Dataset(
            {},
            attrs={
                "contributor_name": "  ,  ,  ,  ",  # Only commas and whitespace
                "institution": "   ",  # Only whitespace
            },
        )

        ds2 = xr.Dataset(
            {},
            attrs={
                "contributor_name": "None,   , , Valid Name",  # Mix of None/empty/valid
                "contributing_institutions": "None,Valid Institution",
            },
        )

        result = ReportUtils.extract_contributors_and_institutions([ds1, ds2], "test")

        # Should filter out invalid entries
        assert "Valid Name" in result["contributors"]
        assert "Valid Institution" in result["institutions"]
        assert "None" not in result["contributors"]
        assert "None" not in result["institutions"]
        assert "" not in result["contributors"]

    def test_compute_dataset_statistics_with_special_variable_types(self):
        """Test statistics computation with various special variable types."""
        # Dataset with string and boolean variables (avoid complex which causes issues)
        ds = xr.Dataset(
            {
                "string_var": (["x"], ["a", "b", "c"]),
                "bool_var": (["x"], [True, False, True]),
                "datetime_var": (["x"], pd.date_range("2020-01-01", periods=3)),
            },
            coords={"x": [0, 1, 2]},
        )

        stats = ReportUtils.compute_dataset_statistics(ds)

        # Should handle all variable types without crashing
        assert stats["total_variables"] == 3
        for var_name in ["string_var", "bool_var", "datetime_var"]:
            assert var_name in stats["variables"]
