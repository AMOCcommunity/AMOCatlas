AMOCarray Format AC1
====================

This document defines the AC1 standard data format produced by the ``amocatlas.convert.to_AC1()`` function.  This format is designed to provide consistency between moored estimates of overturning transport, as from the RAPID, OSNAP, MOVE and SAMBA arrays.

**Relationship to Other Format Documents:**

- :doc:`format_orig` - Documents native data formats from each array
- :doc:`format_conversion` - Describes conversion strategies from native to standardized formats  
- :doc:`format_oceanSITES` - Details OceanSITES compliance requirements
- **This document (format_AC1)** - Specifies the final standardized output format

1. Overview
-----------

The AC1 format improves the interoperability for Atlantic Meridional Overturning Circulation (AMOC) mooring array datasets.  It uses NetCDF (Network Common Data Format) where the software is based on ``xarray.Dataset`` objects.  It is derived from the OceanSITES data format [see here](https://www.ocean-ops.org/oceansites/data/index.html) or [https://www.ocean-ops.org/oceansites/docs/oceansites_data_format_reference_manual.pdf](oceansites_data_format_reference_manual.pdf), but additionally attempts to specify vocabularies.

Note, if the link to the pdf is broken, here is a version downloaded in 2025 [oceansites_data_format_reference_manual.pdf](oceansites_data_format_reference_manual.pdf) which describes OceanSITES version 1.4.

See [oceanSITES format](format_oceanSITES.rst) for some information about how oceanSITES format applies to the datasets collated with `amocatlas`.


2. File Format
--------------

- **File type**: NetCDF4
- **Data structure**: ``xarray.Dataset``
- **Dimensions**:
  - ``N_COMPONENT`` (optional)
  - ``TIME``
  - ``N_LEVELS`` (for vertical)
  - ``N_PROF`` (for a location)
- **Coordinates**:
  - ``TIME`` (required)
  - ``DEPTH`` or ``PRESSURE`` (optional)
  - ``LATITUDE``, ``LONGITUDE`` (optional, where applicable)
- **Encoding**:
  - Default: ``float32`` for data variables
  - Compression: Enabled if saved to NetCDF
  - Chunking: Optional, recommended for large datasets

Note that CF-conventions (https://cfconventions.org/cf-conventions/cf-conventions.html#dimensions) *recommends* that data with the "interpretions of date or time `T`, height or depth `Z`, latitude `Y`, and longitude `X` be used in the relative order `T`, then `Z`, then `Y`, then `X`.  All other dimensions should, whenever possible, be placed to the left of the spatiotemporal dimensions.

3. Variables
------------

.. list-table:: Variables.  The requirement status (RS) is shown in the last column, where **M** is mandatory, *HD* is highly desirable, and *S* is suggested.
   :widths: 20 25 20 20 5
   :header-rows: 1

   * - Name
     - Dimensions
     - Units
     - Description
     - RS
   * - TIME
     - (TIME,)
     - seconds since 1970-01-01
     - Timestamps in UTC
     - **M**
   * - LONGITUDE
     - scalar or (N_PROF,)
     - degrees_east
     - Mooring or array longitude
     - S
   * - LATITUDE
     - scalar or (N_PROF,)
     - degrees_north
     - Mooring or array latitude
     - S
   * - DEPTH or PRESSURE
     - (N_LEVELS,)
     - m
     - Depth levels if applicable
     - S
   * - TEMPERATURE
     - (TIME, ...)
     - degree_Celsius
     - In situ or potential temperature
     - S
   * - SALINITY
     - (TIME, ...)
     - psu
     - Practical or absolute salinity
     - S
   * - TRANSPORT
     - (TIME,)
     - Sverdrup
     - Overturning transport estimate
     - S

4. Global Attributes
--------------------

.. list-table:: Global Attributes
   :widths: 20 20 25 5
   :header-rows: 1

   * - Attribute
     - Example
     - Description
     - RS
   * - title
     - "RAPID-MOCHA Transport Time Series"
     - Descriptive dataset title
     - **M**
   * - platform
     - "moorings"
     - Type of platform
     - **M**
   * - platform_vocabulary
     - "https://vocab.nerc.ac.uk/collection/L06/current/"
     - Controlled vocab for platform types
     - **M**
   * - featureType
     - "timeSeries"
     - NetCDF featureType
     - **M**
   * - id
     - "RAPID_20231231_<orig>.nc"
     - Unique file identifier
     - **M**
   * - contributor_name
     - "Dr. Jane Doe"
     - Name of dataset PI
     - **M**
   * - contributor_email
     - "jane.doe@example.org"
     - Email of dataset PI
     - **M**
   * - contributor_id
     - "ORCID:0000-0002-1825-0097"
     - Identifier (e.g., ORCID)
     - HD
   * - contributor_role
     - "principalInvestigator"
     - Role using controlled vocab
     - **M**
   * - contributor_role_vocabulary
     - "http://vocab.nerc.ac.uk/search_nvs/W08/"
     - Role vocab reference
     - **M**
   * - contributing_institutions
     - "University of Hamburg"
     - Responsible org(s)
     - **M**
   * - contributing_institutions_vocabulary
     - "https://ror.org/012tb2g32"
     - Institutional ID vocab (e.g. ROR, EDMO)
     - HD
   * - contributing_institutions_role
     - "operator"
     - Role of institution
     - **M**
   * - contributing_institutions_role_vocabulary
     - "https://vocab.nerc.ac.uk/collection/W08/current/"
     - Vocabulary for institution roles
     - **M**
   * - source_acknowledgement
     - "...text..."
     - Attribution to original dataset providers
     - **M**
   * - source_doi
     - "https://doi.org/..."
     - Semicolon-separated DOIs of original datasets
     - **M**
   * - amocatlas_version
     - "0.2.1"
     - Version of amocatlas used
     - **M**
   * - web_link
     - "http://project.example.org"
     - Semicolon-separated URLs for more information
     - S
   * - start_date
     - "20230301T000000"
     - Overall dataset start time (UTC)
     - **M**
   * - date_created
     - "20240419T130000"
     - File creation time (UTC, zero-filled as needed)
     - **M**

5. Variable Attributes
----------------------

.. list-table:: Variable Attributes
   :widths: 20 60 5
   :header-rows: 1

   * - Attribute
     - Description
     - RS
   * - long_name
     - Descriptive name of the variable
     - **M**
   * - standard_name
     - CF-compliant standard name (if available)
     - **M**
   * - vocabulary
     - Controlled vocabulary identifier
     - HD
   * - _FillValue
     - Fill value, same dtype as variable
     - **M**
   * - units
     - Physical units (e.g., m/s, degree_Celsius)
     - **M**
   * - coordinates
     - Comma-separated coordinate list (e.g., "TIME, DEPTH")
     - **M**

6. Metadata Requirements
------------------------

Metadata are provided as YAML files for each array. These define variable mappings, unit conversions, and attributes to attach during standardisation.

Example YAML (osnap_array.yml):

.. code-block:: yaml

   variables:
     temp:
       name: TEMPERATURE
       units: degree_Celsius
       long_name: In situ temperature
       standard_name: sea_water_temperature

     sal:
       name: SALINITY
       units: g/kg
       long_name: Practical salinity
       standard_name: sea_water_practical_salinity

     uvel:
       name: U
       units: m/s
       long_name: Zonal velocity
       standard_name: eastward_sea_water_velocity

7. Validation Rules
-------------------

- All datasets must include the TIME coordinate.
- At least one of: TEMPERATURE, SALINITY, TRANSPORT, U, V must be present.
- Global attribute array_name must match one of: ["move", "rapid", "osnap", "samba"].
- File must pass CF-check where possible.

8. Examples
-----------

YAML input: see metadata/osnap_array.yml

Resulting NetCDF Header (excerpt):

.. code-block:: text

   dimensions:
       TIME = 384
       DEPTH = 4

   variables:
       float32 TEMPERATURE(TIME, DEPTH)
           long_name = "In situ temperature"
           standard_name = "sea_water_temperature"
           units = "degree_Celsius"
       ...

   global attributes:
       :title = "OSNAP Array Transport Data"
       :institution = "AWI / University of Hamburg"
       :array_name = "osnap"
       :Conventions = "CF-1.8"

9. Conversion Tool
------------------

To produce AC1-compliant datasets from raw standardised inputs, use:

.. code-block:: python

   from amocatlas.convert import to_AC1
   ds_ac1 = to_AC1(ds_std)

This function:

- Validates standardised input
- Adds metadata from YAML
- Ensures output complies with AC1 format

10. Notes
---------

- Format is extensible for future variables or conventions
- Please cite amocatlas and relevant data providers when using AC1-formatted datasets

11. Provenance and Attribution
------------------------------

To ensure transparency and appropriate credit to original data providers, the AC1 format includes structured global attributes for data provenance.

**Project Funding:**
AC1 format development is supported by the Horizon Europe project EPOC - Explaining and Predicting the Ocean Conveyor (Grant Agreement No. 101081012).

*Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.*

Required Provenance Fields:

.. list-table::
   :widths: 30 60
   :header-rows: 1

   * - Attribute
     - Purpose
   * - source
     - Semicolon-separated list of original dataset short names
   * - source_doi
     - Semicolon-separated list of DOIs for original data
   * - source_acknowledgement
     - Semicolon-separated list of attribution statements
   * - history
     - Auto-generated history log with timestamp and tool version
   * - amocatlas_version
     - Version of amocatlas used for conversion
   * - generated_doi
     - DOI assigned to the converted AC1 dataset (optional)

Example:

.. code-block:: text

   :source = "OSNAP; SAMBA"
   :source_doi = "https://doi.org/10.35090/gatech/70342; https://doi.org/10.1029/2018GL077408"
   :source_acknowledgement = "OSNAP data were collected and made freely available by the OSNAP project and all the national programs that contribute to it (www.o-snap.org); M. Kersalé et al., Highly variable upper and abyssal overturning cells in the South Atlantic. Sci. Adv. 6, eaba7573 (2020). DOI: 10.1126/sciadv.aba7573"
   :history = "2025-04-19T13:42Z: Converted to AC1 using amocatlas v0.2.1"
   :amocatlas_version = "0.2.1"
   :generated_doi = "https://doi.org/10.xxxx/amocatlas-ac1-2025"

YAML Integration (optional):

.. code-block:: yaml

   metadata:
     citation:
       doi: "https://doi.org/10.1029/2018GL077408"
       acknowledgement: >
         M. Kersalé et al., Highly variable upper and abyssal overturning cells in the South Atlantic.
         Sci. Adv. 6, eaba7573 (2020). DOI: 10.1126/sciadv.aba7573
