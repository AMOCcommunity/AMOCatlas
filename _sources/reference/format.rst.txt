AMOCatlas data format
=====================

AMOCatlas writes **OceanSITES-compliant NetCDF files**, following the OceanSITES Data Format
Reference Manual (v1.4). It adds no bespoke file format. Its one addition is a controlled
**short-name vocabulary** for AMOC observing-array quantities (transports, streamfunctions,
component decompositions) that OceanSITES does not define — published separately as ``amocvocab``
(see :doc:`vocabulary`).

.. note::

   This supersedes the earlier "AC-0.1 format". AMOCatlas does not define a variant of OceanSITES
   with documented deviations; its products conform to OceanSITES section 4.2, and the extension is
   a variable vocabulary, not a format. ``AC1``/``AC-0.1`` remains only as a deprecated alias in the
   code for one release.

Which part of OceanSITES applies
--------------------------------

The OceanSITES manual has two scopes. **Section 2** ("NetCDF Data Format for Primary Observational
Data") governs *"individual deployments of moorings, or sometimes repeat ship visits"* — raw
single-deployment data, with required ``site_code``, ``platform_code``, ``data_mode``, a ``DEPTH``
coordinate, and QC flags on every variable.

**AMOCatlas holds none of that.** Every AMOCatlas product is a merged, gridded, or derived quantity,
which the manual handles separately in **section 4.2** ("Data products from OceanSITES data"), and
deliberately loosely. AMOCatlas therefore conforms to section 4.2, and the section-2 deployment
requirements do not apply.

Section 4.2 recognises three kinds of higher-level file, and AMOCatlas's holdings are entirely these:

.. list-table::
   :header-rows: 1
   :widths: 12 88

   * - Type
     - Description and AMOCatlas examples
   * - **LTS**
     - Long time series — multiple deployments concatenated at native resolution (e.g. RAPID
       ``moc_transports``, MOVE, SAMBA).
   * - **GRD**
     - Gridded — binned, averaged, or interpolated onto a grid other than native (e.g. OSNAP gridded
       T/S, RAPID ``ts_gridded``).
   * - **DPR**
     - Derived product — *"derived from multiple sites or some other higher-order processing"* (every
       transport time series and streamfunction, FW2015, Zheng 2024, Calafat 2025).

Section 4.2.1 states the full requirement set, and it is short:

- NetCDF.
- **CF conventions** — a ``standard_name`` is required *when one exists in the CF table* and its
  canonical units are convertible to the reported units; it is omitted otherwise — both when no CF
  name exists, and when a CF name fits the concept but its canonical units are not convertible (for
  example a freshwater transport in ``sverdrup`` against CF's ``kg s-1``, which would misrepresent
  the units). A CF name is never invented.
- **ACDD** discovery metadata.
- Section-2 deployment attributes are *"possible and welcome, as long as they make sense for the data
  product in question"* — i.e. optional, and dropped where they do not apply.
- A list of the lower-level files a product was derived from, with their versions, in ``history`` or
  ``comment``.
- QC flags are *"not strictly required"* for gridded or derived data.
- Information on data mode is *"not strictly required"* for gridded or derived data.

File naming
-----------

AMOCatlas follows the OceanSITES section 4.2.2 higher-level naming convention::

   OS_[PSPANCode]_[StartEndCode]_[ContentType]_[PARTX].nc

- ``OS`` — the OceanSITES prefix.
- ``PSPANCode`` — *"Deployment, platform, site, project, array, or network code."* The manual's
  instruction: *"if all data are from one deployment of one platform, the platform and deployment
  code should be used. Else, move down the sequence terms until one is found that is unique and
  appropriate for all data in the file."* For AMOCatlas an **array or network** code is the right
  choice — e.g. ``RAPID26N``, ``OSNAP``, ``MOVE16N``. This is the documented behaviour for
  multi-platform data, not a deviation, and there is no ``site_code`` requirement on a section-4.2
  file.
- ``StartEndCode`` — the time span, e.g. ``20040402-20240327``.
- ``ContentType`` — a **three-letter** code, one of ``LTS`` / ``GRD`` / ``DPR``, distinguished from
  the one-letter deployment modes (``R``/``P``/``D``) of section-2 files.
- ``PARTX`` — a free content/resolution tag, e.g. ``transports_T12H``.

Example: ``OS_RAPID26N_20040402-20240327_DPR_transports_T12H.nc``.

Dimensions and coordinates
--------------------------

Coordinates use uppercase names. A ``standard_name`` and ``units`` are always set so that files are
machine-identifiable regardless of the coordinate variable name.

.. list-table::
   :header-rows: 1
   :widths: 18 26 16 40

   * - Coordinate
     - CF standard_name
     - Units
     - Description
   * - ``TIME``
     - ``time``
     - ``seconds since 1970-01-01T00:00:00Z``
     - Time coordinate (written from ``datetime64[ns]``).
   * - ``LATITUDE``
     - ``latitude``
     - ``degree_north``
     - Latitude, positive north (WGS84).
   * - ``LONGITUDE``
     - ``longitude``
     - ``degree_east``
     - Longitude, positive east (WGS84).
   * - ``DEPTH``
     - ``depth``
     - ``m``
     - Depth below sea surface, positive downward.
   * - ``PRESSURE``
     - ``sea_water_pressure``
     - ``dbar``
     - Pressure coordinate.
   * - ``SIGMA0``
     - ``sea_water_sigma_theta``
     - ``kg m-3``
     - Potential density anomaly (σ₀); set ``reference_pressure = 0``.
   * - ``SIGMA2``
     - (none — see note)
     - ``kg m-3``
     - Potential density anomaly (σ₂); set ``reference_pressure = 2000``.

.. note::

   CF has no standard name for σ₂. ``SIGMA2`` therefore omits ``standard_name`` and carries its
   meaning in ``long_name`` plus ``reference_pressure = 2000``. ``sea_water_sigma_theta`` is used for
   σ₀ only.

Basin-wide transports have no single position. AMOCatlas gives the array latitude as a scalar
coordinate where it is meaningful (a zonal section at 26°N genuinely has one) and expresses the zonal
extent through ``geospatial_lon_min`` / ``geospatial_lon_max``; it does **not** fabricate a single
``LATITUDE`` value for a section that spans a range.

Units
-----

Units follow UDUNITS-2 so that they parse and convert. Preferred units:

.. list-table::
   :header-rows: 1
   :widths: 34 22 44

   * - Quantity
     - Unit
     - Rationale
   * - Volume transport (MOC, section transports)
     - ``sverdrup``
     - Full spelling; ``Sv`` is the sievert and does not convert to a volume flux.
   * - Heat transport
     - ``PW``
     - Appropriate scale for oceanic heat transport (petawatts).
   * - Freshwater transport
     - ``sverdrup``
     - See note below on ``standard_name``.
   * - Temperature
     - ``degree_C``
     - CF-compliant.
   * - Practical salinity
     - ``1``
     - Dimensionless.
   * - Density / potential density
     - ``kg m-3``
     -
   * - Velocity
     - ``m s-1``
     -
   * - Pressure
     - ``dbar``
     -
   * - Depth
     - ``m``
     - Positive downward.

The unit string is lowercase ``sverdrup``. This is the form UDUNITS-2 recognises (it defines
``sverdrup`` = ``1e6 m3 s-1``; the capitalised ``Sverdrup`` does **not** parse), and it follows the
UDUNITS convention that spelled-out unit names are lowercase while only person-derived symbols are
capitalised. The name "Sverdrup" (after Harald Sverdrup) is still capitalised in prose.

.. note::

   **Freshwater transport omits ``standard_name``.** CF's ``northward_ocean_freshwater_transport`` has
   canonical units ``kg s-1`` (a mass flux). AMOCatlas reports meridional freshwater transport in
   ``Sverdrup`` (a volume flux), which is not convertible to ``kg s-1``; pairing the two would be
   rejected by any CF checker. AMOCatlas therefore reports the value in ``Sverdrup`` and omits the
   ``standard_name``, carrying the meaning in ``long_name``. The same applies to any ``_ERR`` twin.

Global attributes
-----------------

Global attributes are grouped by where the requirement comes from. AMOCatlas does not require the
section-2 deployment attributes (``site_code``, ``platform_code``, ``data_mode``).

**ACDD-required (discovery):** ``title``, ``summary``, ``Conventions``, ``date_created``,
``time_coverage_start``, ``time_coverage_end``, ``geospatial_lat_min`` / ``_lat_max`` /
``geospatial_lon_min`` / ``_lon_max``.

**OceanSITES-recommended (where they make sense):** ``array``, ``naming_authority``, ``id``
(the filename without ``.nc``), ``featureType``, ``source``.

**AMOCatlas-specific (provenance and attribution):** ``contributor_name``, ``contributor_email``,
``contributor_role`` (NERC G04 / ISO 19115 ``CI_RoleCode``), ``contributing_institutions`` and their
EDMO codes, ``source_acknowledgement``, ``source_doi``, ``amocatlas_version``, and a ``history`` entry
recording the source files and versions the product was derived from (section 4.2.1).

Variables
---------

Data variables use uppercase names (e.g. ``MOC``, ``TRANS``, ``MHT``). Each carries ``long_name`` and
``units``; a ``standard_name`` is set **only** when a matching CF standard name exists, and is
otherwise omitted rather than guessed. The short names, their CF ``standard_name`` (or the explicit
absence of one), units, and definitions are the content of :doc:`vocabulary` (the ``amocvocab``
registry).

Worked example (CDL)
--------------------

A derived-product (``DPR``) transport file, conforming to section 4.2 — note the absence of
``site_code`` / ``platform_code`` / ``data_mode``::

   netcdf OS_RAPID26N_20040402-20240327_DPR_transports_T12H {
   dimensions:
       TIME = UNLIMITED ;
   variables:
       double TIME(TIME) ;
           TIME:standard_name = "time" ;
           TIME:units = "seconds since 1970-01-01T00:00:00Z" ;
           TIME:axis = "T" ;
       float LATITUDE ;
           LATITUDE:standard_name = "latitude" ;
           LATITUDE:units = "degree_north" ;
           LATITUDE:axis = "Y" ;
       float MOC(TIME) ;
           MOC:long_name = "Atlantic meridional overturning circulation transport" ;
           MOC:standard_name = "ocean_meridional_overturning_streamfunction" ;
           MOC:units = "sverdrup" ;
           MOC:_FillValue = NaNf ;
       float MFT(TIME) ;
           MFT:long_name = "Meridional freshwater transport" ;
           MFT:units = "sverdrup" ;              // no standard_name: sverdrup not convertible to CF kg s-1
           MFT:_FillValue = NaNf ;

   // global attributes:
           :Conventions = "CF-1.8, ACDD-1.3, OceanSITES-1.4" ;
           :featureType = "timeSeries" ;
           :array = "RAPID" ;
           :naming_authority = "io.github.amoccommunity" ;
           :id = "OS_RAPID26N_20040402-20240327_DPR_transports_T12H" ;
           :title = "RAPID-MOCHA transport time series at 26°N" ;
           :summary = "Meridional overturning and component transports derived from the RAPID array at 26°N." ;
           :geospatial_lat_min = 26.0 ;
           :geospatial_lat_max = 26.0 ;
           :geospatial_lon_min = -80.0 ;
           :geospatial_lon_max = -13.0 ;
           :time_coverage_start = "2004-04-02T00:00:00Z" ;
           :time_coverage_end = "2024-03-27T23:59:59Z" ;
           :contributor_name = "..." ;
           :contributor_role = "principalInvestigator" ;
           :source_doi = "..." ;
           :date_created = "..." ;
           :history = "... : derived from RAPID moc_transports v2023.1 using amocatlas" ;
   }

References
----------

- OceanSITES Data Format Reference Manual v1.4 — the authoritative document, included with AMOCatlas
  at :download:`oceansites_data_format_reference_manual.pdf
  <../_static/oceansites_data_format_reference_manual.pdf>`.
- `CF Conventions <https://cfconventions.org/cf-conventions/cf-conventions.html>`_
- `CF Standard Name Table <https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`_
- `ACDD 1.3 <https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery_1-3>`_
- `UDUNITS-2 <https://docs.unidata.ucar.edu/udunits/current/>`_ — units grammar and the base/derived
  unit database.
- `Ferret ``udunits.dat`` <https://ferret.pmel.noaa.gov/Ferret/documentation/udunits.dat>`_ — a
  reference units database defining oceanographic units. Note ``sverdrup`` (``1e6 m3 s-1``) is defined
  in the UDUNITS-2 database itself (lowercase); ``Sv`` is the sievert and does not convert to a volume
  flux.
