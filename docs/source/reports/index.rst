Data Sources
===============

AMOCatlas provides automated reports for all supported datasets so that you can quickly see the data available, their structure and metadata.  The reports also show variable renaming (for consistency between arrays and other sources), metadata fields edited or added, and a sample figure for a quick look.

.. toctree::
   :maxdepth: 1
   :caption: Individual Dataset Reports

   rapid_report
   osnap_report
   move_report
   samba_report
   mocha_report
   arcticgateway_report
   dso_report
   fbc_report
   fw2015_report
   calafat2025_report
   zheng2024_report
   wh41n_report
   noac47n_report
   nac_report
   sf2021_report
   lebras35n_report
   axmoc22s_report
   axmoc34s_report
   ovide_report
   scotia_report

Report Features
---------------

Each dataset report includes:

📊 **Dataset Overview**
   - Project information and institutional details
   - Temporal coverage and record length
   - Data collection frequency

🔄 **Variable Mapping Table**
   - Original variable names from source files
   - Standardized variable names (for AC1 conversion)
   - Units, descriptions, and statistical summaries

📈 **Statistical Analysis**
   - Min/max values for each variable
   - Missing data percentages
   - Dataset size and structure

Automated Generation
--------------------

Reports are automatically generated from the actual datasets using the command line tool or Python API.

**Command Line Generation:**

Generate reports for all supported arrays::

    python generate_report

Generate report for a specific dataset::

    python generate_report --data_source rapid

Generate reports with custom output directory::

    python generate_report --output_dir custom_reports/

**Python API:**

Reports can also be generated programmatically::

    from amocatlas import report
    
    # Generate report for any dataset
    rst_report = report.generate_dataset_report("rapid", transport_only=True)
    
    # Analyze dataset for programmatic access
    analysis = report.analyze_dataset("rapid", transport_only=True)
    print(f"Dataset has {analysis.statistics['total_variables']} variables")

This ensures the documentation always reflects the current state of the data and
helps identify any missing or incorrect metadata before implementing AC1 conversion.