OceanSITES Format for AMOC Arrays
=================================

This document describes how RAPID, MOVE, OSNAP, and SAMBA array products are mapped into OceanSITES-compliant NetCDF structures within the `amocatlas` package. It summarizes conventions from the OceanSITES format reference manual (v1.4, from 2020) and describes decisions for AMOC-specific implementation.


File naming
--------------

According to OceanSITES, the filenaming convention is: `OS_[PlatformCode]_[DeploymentCode]_[DataMode]_[PARTX].nc`, when applied to individual instrument deployments.

OceanSITES: Gridded and derived data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OceanSITES says a number of higher-level data products can be created:

- **merged:** A "long time series" version that may concatenate multiple deployments (some homogenization).  Not used in `amocatlas`.

- **gridded (GRD):** A "gridded" version which interpolates to a space-time grid different from native instrumental resolution (this is what OSNAP and RAPID provide for their TEMPERATURE and SALINITY fields)

- **derived (DPR):** A "derived" data product (e.g., the "overturning circulation" or "meridional heat transport")


File naming for array data products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`OS_[PSPANCode]_[StartEndCode]_ [ContentType]_[PARTX].nc`

- `PSPANCode`: the `[PlatformCode]` can be replaced with an appropriate choice of site, project, array or network which can be taken from the global attributes of the underlying source data.  For `amocatlas`, we will use the `array` global attribute (should be e.g. RAPID, OSNAP, MOVE, SAMBA, 11South).

- `StartEndCode`: the `[DeploymentCode]` can be replaced with a time range that is appropriate for the data in the file.  For `amocatlas`, this will be the time range of the data in the file. Preferred format is e.g. “20050301-20190831” to indicate data from March 2005 through August 2019.

- `ContentType`: the `[DataMode]` can be replaced with a three-letter code that describes the content of the file (distinguished from the deployment files, which have a one-letter code here), one of:

  - LTS (not used in `amocatlas`): The data are “long time series” data that are essentially at the native instrumental resolution in space and time. The primary difference from the deployment-by-deployment files is that a single file contains merged data from multiple deployments.

  - GRD: The data are “gridded”, meaning that some sort of binning, averaging, interpolating has been done to format the data onto a space-time grid that is different from the native resolution, and more than a simple concatenation like the “LTS” option.  This is what OSNAP and RAPID provide for their TEMPERATURE and SALINITY fields.

  - DPR: The data are a “derived product”, which means that there are data that were derived from multiple sites or some other higher-order processing that the data provider distinguishes from the lower-level data. This is the case for the overturning transports and component transports and streamfunctions.

- [PARTX] - An optional user-defined field for additional identification or explanation of data. For gridded data, this could include the record interval as subfields of ISO 8601 (PnYnMnDTnHnMnS), e.g. P1M for monthly data, T30M for 30 minutes, T1H for hourly.  For `amocatlas`, this will be a short code corresponding to the types of data in the file:

  - RAPID (PSPANCode = RAPID):
    - `ts_gridded.nc` has individual locations with timeSeriesProfile.  The `PARTX` for OceanSITES will be `gridded_mooring`, and ContentType = GRD.
    - `moc_vertical.nc` and `moc_transports.nc` have the streamfunction, and time series of component transports at 12-hour intervals.  The `PARTX` for OceanSITES will combine both and this will be `transports_T12H.nc`, and ContentType = DPR.
    - `2d_gridded.nc` has the 2D gridded data.  The `PARTX` for OceanSITES will be `sections_T10D` for monthly, and ContentType = GRD.
    - `meridional_transports.nc` has the MOC transport in depth and sigma coordinates, as well as MHT and MFT on a 10-day grid. The `PARTX` for OceanSITES will be `transports_T10D.nc`, and ContentType = DPR.

  - OSNAP (PSPANCode = OSNAP):
    - `OSNAP_MOC_MHT_MFT_TimeSeries_201408_202006_2023.nc` has the MOC, MHT and MFT on a monthly grid. `OSNAP_Streamfunction_*nc` has the streamfunction for west, east and all on a monthly and sigma grid.  The `PARTX` for OceanSITES will be `transports_T1M.nc`, with ContentType = DPR.
    - `OSNAP_2D_Gridded_Temperature_Salinity_Velocity_201408_202006.nc` has the 2D gridded data for TEMP, SAL and VELO on TIME, LONGITUDE, LATITUDE and DEPTH.  The `PARTX` for OceanSITES will be `sections_T1M.nc`, with ContentType = GRD.

  - MOVE (PSPANCode = MOVE):
    - `OS_MOVE_TRANSPORTS.nc` has the total transport in a layer 1200-4950 dbar, the internal, offset and boundary transports.  The `PARTX` for OceanSITES will be `transports_T1M.nc`, with ContentType = DPR.

  - SAMBA (PSPANCode = SAMBA):
    - `Upper_Abyssal_Transport_Anomalies.txt` has the upper and abyssal transport anomalies. The `PARTX` for OceanSITES will be `Kersale_transports_T1M.nc`, with ContentType = DPR.
    - `MOC_TotalAnomaly_and_constituents.asc` has the MOC total anomaly and constituents/components. The `PARTX` for OceanSITES will be `Meinen_transports_T1M.nc`, with ContentType = DPR.

  Unclear whether to call "Meinen" the "2site" and "Kersale" the "9site".


Feature Types
~~~~~~~~~~~~

The following OceanSITES featureTypes are used:

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Feature Type
     - Used For
     - Description
   * - ``timeSeries``
     - MOC, MHT, MFT, Ekman
     - 1D time series at a single or derived location
   * - ``timeSeriesProfile``
     - T/S profiles at fixed mooring locations
     - Includes depth and time as dimensions
   * - ``timeSeriesProfile``
     - Interpolated sections from OSNAP, RAPID, SAMBA
     - Regular grids in depth/longitude or density/longitude
   * - ``timeSeriesProfile``
     - Streamfunction, MOC decompositions
     - Derived products, not raw observations

------------------------------------------------------------------------

Global Metadata
---------------

The following global attributes are recommended for OceanSITES-compliant NetCDF files. The ``RS`` column indicates the requirement status:

- **M** = Mandatory (required for compliance or by GDAC)
- *HD* = Highly Desired (strongly recommended)
- *S* = Suggested (optional but useful)



- Unidata Attribute Convention for Data Discovery (ACDD).  See [here](https://www.esipfed.org/what-is-acdd/).

- Additional metadata attributes from the deployment-by-deployment files (as
specified earlier in this document) are possible and welcome, as long as they
make sense for the data product in question.

1. Discovery and Identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following global attributes are recommended for inclusion in all OceanSITES-compliant NetCDF files. This table includes both required and suggested metadata fields relevant for data discovery, attribution, and catalog integration.

.. list-table:: Global Attributes for Discovery and Identification
   :widths: 19 40 28 7
   :header-rows: 1

   * - Attribute Name
     - Definition
     - Example
     - RS
   * - ``site_code``
     - Name of the OceanSITES site. Technically, site codes should be approved by the OceanSITES Project Office to avoid duplication.
     - **one of:**
        - "RAPID"
        - "MOVE"
        - "OSNAP"
        - "SAMBA"
        - or ""
     - **M** (for GDAC)
   * - ``data_mode``
     - Indicates if data are real-time (``R``), provisional (``P``), or delayed-mode (``D``).
     - ``D``
     - **M** (for GDAC)
   * - ``title``
     - Short, human-readable phrase or sentence describing the dataset.
     - **ex.:**
        - "Ocean transports at 26°N"
        - "Hydrographic sections data at 26°N"
        - "Oceanographic section data at OSNAP line"
        - "Ocean transports at MOVE 16°N line"
        - "Ocean transports at SAMBA 34.5°S line"
     - *HD*
   * - ``theme``
     - List of OceanSITES theme areas to which this dataset belongs (comma separated, see reference manual for options). *Omitted for datasets not derived from moored observations.*
     - **ex.:** "Transport Moored Arrays"
     - *S*
   * - ``naming_authority``
     - A unique name that identifies the institution or organisation who provided the id.  ACDD-1.3 recommends using reverse-DNS naming.
     - **ex.:**
        - "OceanSITES"
     - *S*
   * - ``array``
     - OceanSITES array grouping based on scientific rationale. Note that this will be part of the ``id`` and filename.
     - **ex.:** "RAPID"
     - **M**
   * - ``id``
     - Unique dataset ID (often filename without `.nc`, which would be "OS_<array>_<YYYYMMDD>-<YYYYMMDD>_<GRD/DPR>_<PARTX>" where <array> is one of "RAPID", "MOVE", etc, the datestrings are the start and end dates of the dataset, GRD for gridded data, DPR for derived products, and the PARTX is some unique combination of "transports_T1M" or "sections_T10D" or similar).
     - **ex.:**
        - "OS_RAPID_20040401-20230211_DPR_transports_T10D"
        - "OS_OSNAP_20140801-20200601_GRD_sections_T1M"
     - **M**
   * - ``summary``
     - Longer free-format text describing the dataset. This attribute should allow data discovery for a human reader. A paragraph of up to 100 words is appropriate. (ACDD)
     - "Oceanographic mooring data from the RAPID array at 26°N in the Atlantic since 2004.  Measured properties: temperature, salinity at 20 dbar intervals and 10-day intervals."
     - *S*
   * - ``source``
     - Use a term from the `SeaVoX Platform Categories vocabulary (L06) <https://vocab.nerc.ac.uk/collection/L06/current/>`_ list, usually one of the following: “moored surface buoy”, “subsurface mooring”, ”ship” (CF)
     - **ex.:**
        - "subsurface mooring"
        - "orbiting satellite"
        - "drifting subsurface profiling float"
        - "autonomous underwater vehicle"
        - "coastal structure"
        - "fixed benthic node"
        - "research vessel" or "ship"
     - *HD*
   * - ``principal_investigator``
     - Name of the person responsible for the scientific project.  Multiple PIs are separated by commas.
     - **ex.:** "Alice Juarez, John Smith"
     - **M**
   * - ``principal_investigator_email``
     - Email address of the PI.
     - **ex.:** "ajuarez@whoi.edu, john.smith@noc.ac.uk"
     - *S*
   * - ``principal_investigator_id``
     - ORCiD or other persistent ID for the PI.
     - **ex.:** "https://orcid.org/0000-0001-5044-7079, "
     - **M**
   * - ``creator_name``
     - Name of the person (or group) who created the dataset.  Multiple creators are separated by commas.
     - **ex.:** "Alice Juarez"
     - *S*
   * - ``creator_email``
     - Email address of the creator.
     - **ex.:** "ajuarez@whoi.edu"
     - *S*
   * - ``creator_id``
     - ORCiD or other persistent ID for the creator.
     - **ex.:** "https://orcid.org/0000-0001-5044-7079"
     - *S*
   * - ``creator_type``
     - Describes the creator entity: ``person``, ``group``, ``institution``, or ``position``.
     - **ex.:** "institution"
     - *S*
   * - ``creator_institution``
     - Institution associated with the creator.
     - **ex.:** "WHOI"
     - *S*
   * - ``keywords_vocabulary``
     - Vocabulary source for keywords. E.g. `GCMD Science Keywords <https://gcmd.earthdata.nasa.gov/KeywordViewer/>`_.
     - **ex.:** "GCMD Science Keywords"
     - *S*
   * - ``keywords``
     - Provide comma-separated list of terms that will aid in discovery of the dataset. (ACDD)
     - **ex.:** "EARTH SCIENCE > Oceans > Ocean Circulation > Thermohaline Circulation"
     - *S*
   * - ``comment``
     - Miscellaneous information about the data or methods used to produce it. Any free-format text is appropriate. (CF)
     - **ex.:** "Preliminary version; subject to revision"
     - *S*
   * - ``platform_code``
     - A unique platform code.  This code is either assigned by the site PI (see principal_investigator) or by the data provider.
     - Note that this is required for OceanSITES for GDAC, but it is not implemented in the current version of the `amocatlas` package.
     - **M** (for GDAC)
   * - ``principal_investigator_url``
     - Web URL for the PI.
     - "https://whoi.edu/profile/ajuarez"
     - *S*
   * - ``creator_url``
     - Web profile for the creator.
     - **ex.:** "https://whoi.edu/profile/ajuarez"
     - *S*
   * - ``network``
     - A grouping of sites based on common shore-based logistics, funding, or infrastructure.
     - **ex.:** "EuroSITES"
     - *S*

2. Geo-spatial-temporal Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following attributes are recommended for inclusion in all OceanSITES-compliant NetCDF files. This table includes both required and suggested metadata fields relevant for data discovery, attribution, and catalog integration.

.. list-table:: Geo-spatial-temporal Metadata
   :widths: 19 40 28 7
   :header-rows: 1

   * - Attribute Name
     - Definition
     - Example
     - RS
   * - ``sea_area``
     - Geographical coverage. `SeaVox Water Body Gazetteer vocabulary (C19) <https://vocab.nerc.ac.uk/collection/C19/current/>`_
     - **ex.:**
        - "North Atlantic Ocean"
        - "South Atlantic Ocean"
        - "Arctic Ocean"
     - *S*
   * - ``geospatial_lat_min``
     - The southernmost latitude, a value between -90 and 90 degrees; may be string or numeric. (ACDD, GDAC)
     -
        - **ex.:** geospatial_lat_min = 20.0
        - **format:** decimal degree
     - **M** (for GDAC)
   * - ``geospatial_lat_max``
     - The northernmost latitude, a value between -90 and 90 degrees; may be string or numeric. (ACDD, GDAC)
     -
        - **ex.:** geospatial_lat_max = 20.0
        - **format:** decimal degree
     - **M** (for GDAC)
   * - ``geospatial_lat_units``
     - Must conform to `udunits <https://www.unidata.ucar.edu/software/udunits/>`_. If not specified then ”degree_north” is assumed. (ACDD)
     - **ex.:** geospatial_lat_units =  "degrees_north"
     - *S*
   * - ``geospatial_lon_min``
     - The westernmost longitude, a value between -180 and 180 degrees. (ACDD, GDAC)
     - **ex.:** geospatial_lon_min = -80.0
     - **M** (for GDAC)
   * - ``geospatial_lon_max``
     - The easternmost longitude, a value between -180 and 180 degrees. (ACDD, GDAC)
     -
        - **ex.:** geospatial_lon_max = 20.0
        - **format:** decimal degree
     - **M** (for GDAC)
   * - ``geospatial_lon_units``
     - Must conform to `udunits <https://www.unidata.ucar.edu/software/udunits/>`_. If not specified then ”degree_east” is assumed. (ACDD)
     - **ex.:** geospatial_lon_units = "degrees_east"
     - *S*
   * - ``geospatial_vertical_min``
     - The minimum depth or height of the data, a value between -10000 and 10000 meters. Describes the numerically smaller vertical limit. (ACDD)
     -
        - **ex.:** geospatial_vertical_min = 0.0
        - **format:** meter depth
     - **M** (for GDAC)
   * - ``geospatial_vertical_max``
     - The maximum depth or height of the data, a value between -10000 and 10000 meters. Describes the numerically larger vertical limit. (ACDD)
     -
        - **ex.:** geospatial_vertical_max = 0.0
        - **format:** meter depth
     - **M** (for GDAC)
   * - ``geospatial_vertical_positive``
     - Indicates which direction is positive; "up" means that z represents height, while a value of "down" means that z represents pressure or depth. If not specified then “down” is assumed. (ACDD)
     - **ex.:** geospatial_vertical_positive = "down"
     - *S*
   * - ``geospatial_vertical_units``
     - Units of depth, pressure, or height. If not specified then “meter” is assumed. (ACDD)
     - **ex.:** geospatial_vertical_units = "m"
     - *S*
   * - ``time_coverage_start``
     - Datetime of the first measurement in this dataset in ISO 8601 format. (ACDD)
     -
        - **ex.:** time_coverage_start = "2004-01-01T00:00:00Z"
        - **format:** formatted string, ISO 8601
     - **M** (for GDAC)
   * - ``time_coverage_end``
     - Datetime of the last measurement in this dataset in ISO 8601 format. (ACDD)
     -
        - **ex.:** time_coverage_end = "2023-01-01T00:00:00Z"
        - **format:** formatted string, ISO 8601
     - **M** (for GDAC)
   * - ``time_coverage_duration``
     - Use ISO 8601 ‘duration’ convention (ACDD)
     - **ex.:**
        - "P415D" (415 days)
        - "P1Y" (1 year)
        - "P1Y2M" (1 year, 2 months)
     - *S*
   * - ``time_coverage_resolution``
     - The time interval between records: Use ISO 8601 (PnYnMnDTnHnMnS). (ACDD)
     -
        - **ex.:** time_coverage_resolution = "P1D" (1 day)
        - **format:** formatted string, ISO 8601
     - *S*
   * - ``featureType``
     - for files using the Discrete Sampling Geometry, available in CF-1.5 and later. See CF documents. For OceanSITES, this should be one of: ``timeSeries``, ``timeSeriesProfile``, ``trajectory``.
     - **ex.:**
        - "timeSeries"
        - "timeSeriesProfile"
     - *M*
   * - ``data_type``
     - From Reference table 1: OceanSITES specific. (GDAC)
     - **ex.:**
        - ”OceanSITES time-series data”
     - *M*

3. Conventions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Conventions used
   :widths: 19 40 28 7
   :header-rows: 1

   * - Attribute Name
     - Definition
     - Example
     - RS
   * - ``format_version``
     - OceanSITES format version
     - **ex.:**  1.4
     - **M**
   * - ``Conventions``
     - Name of the conventions used in the dataset.
     - **ex.:** "CF-1.7, OceanSITES-1.4, ACDD-1.2"
     - *S*

4. Publication Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Publication information
   :widths: 19 40 28 7
   :header-rows: 1

   * - Attribute Name
     - Definition
     - Example
     - RS
   * - ``publisher_name``
     - Name of the person responsible for metadata and formatting
     - **ex.:** "AMOCarray Development Team"
     - *S*
   * - ``publisher_url``
     - Web address of the institution or data publisher
     - **ex.:** "http://github.com/AMOCcommunity/amocatlas"
     - *S*
   * - ``references``
     - Published or web-based references that describe the data or methods used to produce it. Include a reference to OceanSITES and a project-specific reference if appropriate.
     - **ex.:**
        - ”http://www.oceansites.org, http://www.noc.soton.ac.uk/animate/index.php”
     - *S*
   * - ``license``
     - A statement describing the data distribution policy; it may be a project- or DAC-specific statement, but must allow free use of data. OceanSITES has adopted the CLIVAR data policy, which explicitly calls for free and unrestricted data exchange. Details at: http://www.clivar.org/resources/data/data-policy (ACDD)
     - **ex.:**
        - "Follows CLIVAR (Climate Varibility and Predictability) standards, cf. http://www.clivar.org/resources/data/data-policy. Data available free of charge. User assumes all risk for use of data. User must display citation in any publication or product using data. User must contact PI prior to any commercial use of data."
        - "CC-BY-4.0"
     - *S*
   * - ``citation``
     - The citation to be used in publications using the dataset; should include a reference to OceanSITES, the name of the PI, the site name, platform code, data access date, time, and URL, and, if available, the DOI of the dataset.
     - **ex.:** "These data were collected and made freely available by the OceanSITES program and the national programs that contribute to it."
     - *S*
   * - ``acknowledgement``
     - A place to acknowledge various types of support for the project that produced this data. (ACDD)
     - **ex.:**
        - acknowledgement=”Principal funding for the NTAS experiment is provided by the US NOAA Climate Observation Division.”
     - *S*

5. Provenance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. list-table:: Provenance
   :widths: 19 40 28 7
   :header-rows: 1

   * - Attribute Name
     - Definition
     - Example
     - RS
   * - ``date_created``
     - The date on which the this file was created. Version date and time for the data contained in the file. See note on time format below. (ACDD)
     - **ex.:** date_created =”2016-04-11T08:35:00Z”
     - **M**
   * - ``date_modified``
     - The date on which this file was last modified. (ACDD)
     - **ex.:** date_modified =”2016-04-11T08:35:00Z”
     - *S*
   * - ``history``
     - Provides an audit trail for modifications to the original data. It should contain a separate line for each modification, with each line beginning with a timestamp, and including user name, modification name, and modification arguments. The time stamp should follow the format outlined in the note on time formats below. (NUG)
     - **ex.:** history= "2012-04-11T08:35:00Z data collected, A. Meyer; 2012-04-12T10:15:00Z quality control applied, B. Smith"
     - *S*
   * - ``processing_level``
     - Level of processing and quality control applied to data. Preferred values are listed in reference table 3.
     - processing_level = ”Data verified against model or other contextual information” (OceanSITES specific)
     - *S*
   * - ``QC_indicator``
     - A value valid for the whole dataset
     - **ex.:**
        - "unknown" (no QC done, no known problems)
        - "excellent" (no known problems, all important QC done)
        - "probably good" (validation phase)
        - "mixed" (some problems, see variable attributes)
     - *S*
   * - ``contributor_name``
     - A semi-colon-separated list of names of any individuals or institutions that contributed to the collection, editing or publication of the data in the file. (ACDD)
     - **ex.:** "Alice Juarez; John Smith"
     - *S*
   * - ``contributor_role``
     - The roles of any individuals or institutions that contributed to the creation of this data, separated by semi-colons (ACDD)
     - **ex.:** "data collector; data editor"
     - *S*
   * - ``contributor_email``
     - The email addresses of any individuals or institutions that contributed to the creation of this data, separated by semi-colons (ACDD)
     - **ex.:** "alicejuarez@whoi.edu; johnsmith@noc.ac.uk"
     - *S*

Dimension and definition
-------------------

OceanSITES recommends coordinates with an "axis" attribute defining that they represent the X, Y, Z or T axis (which should appear in the relative order T, Z, Y, X). Here, they use the naming: `TIME`, `LATITUDE`, `LONGITUDE`, and `DEPTH`.   (**Note: this departs from OSNAP data files**).  Apparently in OceanSITES, "depth" is strongly preferred over "pressure".

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Dimension
     - Definition
     - Comment
   * - ``TIME``
     - unlimited, axis="T"
     - Time coordinate in days since 1950-01-01
   * - ``LEVEL``
     - vertical, axis="Z"
     - Positive downward, in meters
   * - ``LATITUDE``, ``LONGITUDE``
     - horizontal, axis="Y", axis="X"
     - In degrees north/east


Coordinates
-----------------
.. list-table::
   :widths: 25 50 7
   :header-rows: 1

   * - Coordinate name
     - Coordinate attributes
     - RS
   * - ``TIME``
        - data type: double (datetime64[ns])
        - dimension: ``TIME``
     -
        - long_name = "Time elapsed since 1970-01-01T00:00:00Z"
        - calendar = "gregorian";
        - units = "seconds since 1970-01-01T00:00:00Z";
        - axis = "T"
     - **M**
   * - ``DEPTH`` or ``PRESSURE`` or ``SIGMA``
        - data type: double (float32)
        - dimension: ``LEVEL``
     -
        - long_name = "Depth below surface of the water body"
        - standard_name = "depth" or "sea_water_pressure" or "sea_water_sigma_theta"
        - positive = "down" or "down" or "down"
        - units = "m" or "dbar" or "kg m-3"
        - valid_min = 0.0 or 0.0 or 0.0
        - valid_max = 10000.0 or 10000.0 or 50.0
        - axis = "Z"
     - *S*
   * - ``LONGITUDE``
        - data type: double (float32)
        - dimension: ``LONGITUDE``
     -
        - long_name = "Longitude"
        - standard_name = "longitude"
        - units = "degrees_east"
        - valid_min = -180.0
        - valid_max = 180.0
        - axis = "X"
     - *S*
   * - ``LATITUDE``
        - data type: double (float32)
        - dimension: ``LATITUDE``
     -
        - long_name = "Latitude"
        - standard_name = "latitude"
        - units = "degrees_north"
        - valid_min = -90.0
        - valid_max = 90.0
        - axis = "Y"
     - *S*

For Time, by default, it represents the *center of the data sample or averaging period*.  This is not consistent with OSNAP native format.

Geophysical variables
-------------------

All variables must follow CF and OceanSITES standard_name rules (lowercase, underscores, no capitals).

Use ``standard_name`` where defined; otherwise, include descriptive ``long_name`` and appropriate ``units``.

.. list-table::
   :widths: 19 40 28 7
   :header-rows: 1

   * - VARIABLE NAME
     - variable attributes
     - Example
     - RS
   * - ``<PARAM>``
        - data type: float
        - dimensions: (``TIME``, ``LEVEL``, ``LONGITUDE``)
     -
        - <PARAM>:long_name = "<X>"
        - <PARAM>:standard_name = "<X>"
        - <PARAM>:vocabulary = "";
        - <PARAM>:_FillValue = <X>
        - <PARAM>:units = "<X>"
        - <PARAM>:ancillary_variables = "<PARAM>_QC";
        - <PARAM>:coordinates = "TIME, LEVEL, LONGITUDE"
     - ``CT(TIME, LEVEL, LONGITUDE)``
        - long_name = "Conservative temperature"
        - standard_name = "sea_water_conservative_temperature"
        - vocabulary = "https://vocab.nerc.ac.uk/collection/P07/current/IFEDAFIE/"
        - units = "degree_Celsius"
        - valid_min = -2.0
        - valid_max = 35.0
        - _FillValue = NaNf
        - coordinates = "TIME, LEVEL, LONGITUDE"
     - *S*



Flags and QC
~~~~~~~~~~~~~~~~~~~~~
For Flags, these are indicated as **<PARAM>_QC** with standard values "flag_values" = 0, 1, 2, 3, 4, 7, 8, 9 and "flag_meanings" = "unknown good_data probably_good_data potentially_correctable_bad_data bad_data nominal_value interpolated_value missing_value" (attribute to the variable) defined.  There is also an optional **<PARAM>_UNCERTAINTY** with "technique_title" as "Title of the document that describes the technique that was applied to estimate the uncertainty of the data".  I'm not sure whether either of these applies to the "_FLAG" for RAPID or the "_ERR" for OSNAP.  But OSNAP does have the "QC_indicator" and "Processing_level".  QC_indicator is OceanSITES specific (see table 2) and "processing_level" is table 3.

The QC_indicator (ref table 2) are used in the <PARAM>_QC variable to describe the quality of each measurement.  I'm not sure this is how OSNAP uses it.  Processing level options applied to all measurements of a variable and are given as an overall indicator in the attributes of each variable:

- Raw instrument data

- Instrument data that has been converted to geophysical values

- Post-recovery calibrations have been applied

- Data has been scaled using contextual information

- Known bad data has been replaced with null values

- Known bad data has been replaced with values based on surrounding
data

- Ranges applied, bad data flagged

- Data interpolated

- Data manually reviewed

- Data verified against model or other contextual information

- Other QC process applied


AMOC array data
---------------

- RAPID data files use dimensions of `depth` and `time` but coordinates of `pressure` in the 12-hourly data.  In the 10-day data, it is `time`, `longitude`, and `depth` and also `sigma0` for dimensions, with coordinates of `pressure` and `sigma0`.(**Verify this**).  Dimension orders do not follow CF conventions so arrays will need to be rotated.  Axis is not specified (needs to be added).

- OSNAP data files use dimensions of `TIME`, `LEVEL`, `LATITUDE` and `LONGITUDE` and sometimes also `DEPTH`.  Axis is specified.  The order of dimensions is consistent with OceanSITES.  Standard names are missing for some variables (e.g., the T_ALL and `sea_water_velocity` doesn't seem to be an option in CF.  Probably because we need a version like `sea_water_velocity_across_line`.)  We can use `ocean_meridional_overturning_streamfunction` for the streamfunction, and perhaps `ocean_volume_transport_across_line` which is in CF conventions and is what MOVE uses.

- MOVE data files use dimensions of `TIME` only.   Standard names are missing for some variables (e.g., the `transport_component_internal` and `transport_component_internal_offset` and `transport_component_boundary`).  CF standard names does have `baroclinic_northward_sea_water_velocity` so perhaps we can use `baroclinic_transport_across_line`.

- SAMBA data files are also in `TIME` only.  Standard names are everywhere `Transport_anomaly`. CF conventions allows adding `_anomaly` but then it should be something like `ocean_volume_transport_anomaly_across_line` or something similar.


References
------------
Relevant references:

- `OceanSITES data format <https://www.ocean-ops.org/oceansites/data/index.html>`_

- `OceanSITES data format reference manual <https://www.ocean-ops.org/oceansites/docs/oceansites_data_format_reference_manual.pdf>`_, but additionally attempts to specify vocabularies. Note, if the link to the pdf is broken, here is a version downloaded in 2025: :download:`oceansites_data_format_reference_manual.pdf </_static/oceansites_data_format_reference_manual.pdf>` which describes OceanSITES version 1.4.

- `UDUNITS-2 <https://docs.unidata.ucar.edu/udunits/current/>`_, or the local extract :doc:`AC1_units </AC1_units>`

- Vocabularies are primarily CF standard names. See :doc:`AC1_standard_names </AC1_standard_names>`.

- CF conventions has a number of relevant sections, including:

  - `CF conventions <https://cfconventions.org/cf-conventions/cf-conventions.html>`_

  - `CF standard names <https://cfconventions.org/cf-conventions/cf-standard-names.html>`_

  - `CF units <https://cfconventions.org/cf-conventions/cf-conventions.html#units>`_

  - `CF coordinate reference system <https://cfconventions.org/cf-conventions/cf-conventions.html#coordinate-reference-system>`_

  - `CF discrete sampling geometries <https://cfconventions.org/cf-conventions/cf-conventions.html#discrete-sampling-geometries>`_
