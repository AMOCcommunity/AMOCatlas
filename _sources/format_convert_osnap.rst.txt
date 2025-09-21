.. _convert-osnap:
OSNAP conversion thoughts
----------------------

At OSNAP, we have variables like MOC_ALL, MOC_EAST and MOC_WEST which are time series (``TIME``), but these could be represented as MOC (``N_PROF``, ``TIME``) where instead of the three different variables, N_PROF=3.  This would be somewhat more difficult to communicate to the user, since LATITUDE and LONGITUDE are not single points per N_PROF but instead may represent end points of a section.

Variables MOC_ALL_ERR are also provided, which could be translated to MOC_ERR (``N_PROF``, ``TIME``) with LATITUDE (``N_PROF``) or LATITUDE_BOUND (``N_PROF``, 2).

Heat fluxes also exist, as MHT_ALL, MHT_EAST and MHT_WEST, so these could be MHT (``N_PROF``, ``TIME``).




Potential reformats:
~~~~~~~~~~~~~~~~~~~~~

- **Overturning:**
  - ``MOC`` and ``MOC_ERR``: time series (dimension: ``TIME``, ``N_LOCATION``=3) where ``N_LOCATION``=3 (e.g. MOC_ALL, MOC_EAST, MOC_WEST)

  - ``STREAMFUNCTION``: (``TIME``, ``N_LEVELS``, ``N_PROF``=3) - This would be from ``OSNAP_Streamfunction_201408_202006_2023.nc`` and is the overturning streamfunction in sigma-theta coordinates.

  - ``MHT`` and ``MHT_ERR``: same dimensions as ``MOC``

  - ``MFT`` and ``MFT_ERR``: same dimensions as ``MOC``

  - ``LATITUDE_BOUND``: (``N_LOCATION``, 3) - this would be the latitude bounds for the west, east and full.

  - ``LONGITUDE_BOUND``: (``N_LOCATION``, 3) - this would be the longitude bounds for the west, east and full.


- **Gridded sections:** ``TEMPERATURE``, ``SALINITY``, ``VELOCITY``

  - Dimensions: ``TIME``, ``N_PROF``, ``N_LEVELS`` (71, depth=199, longitude=256)

  - Coordinates: ``LATITUDE``, ``LONGITUDE`` (``N_PROF``=longitude grid,), ``TIME`` in datetime.  And ``DEPTH`` (``N_LEVELS``,)

  - Variables: ``TEMPERATURE``, ``SALINITY``, ``VELOCITY`` (``TIME``, ``N_PROF``, ``N_LEVELS``).  Attributes would specify units and the version of temperature/salinity.   and specifying what version of temperature/salinity.   The flags would have an attribute describing what the values mean (e.g. "1=good, 2=bad, etc").

