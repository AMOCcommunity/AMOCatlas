.. _convert-rapid:
RAPID conversion thoughts
--------------------------


For example, at 26°N, the RAPID array produces an AMOC transport time series (volume transport in depth space) which is a 1-dimensional time series with a single registered latitude (26.5) and no registered longitude.  It also provides profiles of temperature, salinity and dynamic height representing individual locations (single latitude, single nominal longitude) on a vertical grid of 20 dbar.  Several locations are provided, with names like WB, MAR_WEST, MAR_EAST, EB.  So there are N_PROF locations, with N_LEVELS and also TIME as dimensions. And the LATITUDE would be ``N_PROF`` (a small number, like 4, representing mooring locations)

More recently, they have started providing a section of temperature, saliity and velocity which are then N_PROF, TIME and N_LEVELS, but now the ``N_PROF`` (and both ``LONGITUDE`` and ``LATITUDE``) would be on a regular grid--or at least with more locations (longer N_PROF), though it's possible LATITUDE would be a single latitude (26.5).

RAPID also provides layer transports which are single time series with names like t_therm10, t_aiw10, t_ud10, t_ld10, etc, which are between specified depth ranges.  These could be simply: ``TRANSPORT`` (``N_LEVELS``, ``TIME``) with ``DEPTH_BOUND`` (``N_LEVELS``, 2) to give an upper and lower bound on the depths used to produce transport in layers?  It would also need something like ``TRANSPORT_NAME`` (``N_LEVELS``) of type string.

Check CF conventions for standard names: https://github.com/cf-convention/vocabularies/issues.  Note that **standard names** consist of lower-letters, digits and underscores, and begin with a letter. Upper case is not used.  See [here](https://cfconventions.org/Data/cf-standard-names/docs/guidelines.html).


- ``moc_vertical.nc``:

  - **Convert to OceanSITES:** Here, we should change the dimension to all-caps ``DEPTH`` and ``TIME``.  Units on the streamfunction should be `Sverdrup` (full spelling to avoid confusion with `Sv` for sievert). According to OceanSITES, the order of the variables should be T, Z, Y, X, so the streamfunction should be (``TIME``, ``DEPTH``).  The filename should be something like ``OS_RAPID_YYYYMMDD-YYYYMMDD_DPR_mocvertical_T12H.nc``. Here, we are using the ``OS`` prefix, ``RAPID`` as the PlatformCode, the date start and end for the DeploymentCode, and the data mode is ``DPR`` for derived product.  The PARTX field combines the content type and time resolution.

- ``ts_gridded.nc``:

- **Convert to OceanSITES:** Dimensions should be ``TIME`` and ``DEPTH`` (in T, Z order), where the coordinate name can be ``PRES`` for ``pressure``.  The featureType global attribute can be ``timeSeriesProfile``.

- ``moc_transports.nc``:

- ``meridional_transports.nc``:

Potential reformats:
~~~~~~~~~~~~~~~



**Key Products**:

- **Overturning:**
  - ``MOC``: time series (dimension: ``TIME``)

  - ``STREAMFUNCTION``: (``TIME``, ``DEPTH``) - this is the vertical profile of MOC (originally ``stream_function_mar`` in ``moc_vertical.nc``, note that this extends deeper than the depth grid in ``ts_gridded.nc`` due to the incorporation of an AABW profile).

- **Profiles:** ``TEMPERATURE``, ``SALINITY``, vertically gridded at mooring locations.

  - Dimensions: ``TIME``, ``N_PROF``, ``N_LEVELS`` (T, Y/X, Z order)

  - Coordinates: ``LATITUDE``, ``LONGITUDE`` (``N_PROF``=5,) - these would be the locations of the profiles, which are current in the "long name" for each of the ``TG_west``, ``TG_east``, ``TG_wb3``, ``TG_MARWEST``, ``TG_mareast``.  etc. ``TIME`` in datetime.  And ``PRESSURE`` (``N_LEVELS``,) - this is the depth grid in ``ts_gridded.nc``.

  - Variables: ``TEMPERATURE``, ``SALINITY``, ``TEMPERATURE_FLAG``, ``SALINITY_FLAG`` (``TIME``, ``N_PROF``, ``N_LEVELS``).  Attributes would specify units and the version of temperature/salinity.   and specifying what version of temperature/salinity.   The flags would have an attribute describing what the values mean (e.g. "1=good, 2=bad, etc").

- **Gridded sections:** ``TEMPERATURE``, ``SALINITY``, ``VELOCITY``

  - Dimensions: ``TIME``, ``N_PROF``, ``N_LEVELS`` (T, Y/X, Z order)

  - Coordinates: ``LATITUDE``, ``LONGITUDE`` (``N_PROF``=longitude grid,), ``TIME`` in datetime.  And ``PRESSURE`` (``N_LEVELS``,)

  - Variables: ``TEMPERATURE``, ``SALINITY``, ``VELOCITY`` (``TIME``, ``N_PROF``, ``N_LEVELS``).  Attributes would specify units and the version of temperature/salinity.   and specifying what version of temperature/salinity.   The flags would have an attribute describing what the values mean (e.g. "1=good, 2=bad, etc").

- **Layer transports:**

  - Dimensions: ``TIME``, ``N_LEVELS`` (T, Z order)

  - Coordinates: ``LATITUDE``, ``LONGITUDE_BOUNDS`` (scalar, x2), ``TIME`` in datetime.  And ``DEPTH_BOUND`` (``N_LEVELS``, 2) - this would be the depth bounds for the transport layers.

  - Variables: ``TRANSPORT`` (``TIME``, ``N_LEVELS``) - this would be the time series of transport in layers.  This would also have ``DEPTH_BOUND`` (``N_LEVELS``, 2) to give an upper and lower bound on the depths used to produce transport in layers.  It would also need something like ``TRANSPORT_NAME`` (``N_LEVELS``, string) to indicate what the layer is (e.g. `t_therm10`, `t_aiw10`, etc).

- **Component transports:**

  - Dimensions: ``TIME``, ``N_COMPONENT`` (T, component order)

  - Coordinates: ``LATITUDE``, ``LONGITUDE_BOUNDS`` (scalar, x2), ``TIME`` in datetime.  ``N_COMPONENT`` for the number of components.

  - Variables: ``TRANSPORT`` (``TIME``, ``N_COMPONENT``) -  This would also have ``TRANSPORT_NAME`` (``N_COMPONENT``, string) to indicate what the component is (e.g. `t_gs10`, `t_ek10`, etc).  This would be similar to the layer transport but without the depth bounds.
