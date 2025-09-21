.. This file is included under 'format_orig.rst' and should use '~~' or lower as the top header level.

.. _array-fw2015:

FW2015 Original Data Format
---------------------------

This is a different beast but similar to RAPID in that it has components which represent transport for different segments of the array (like Gulf Stream, Ekman and upper-mid-ocean) where these sum to produce MOC. This is *vaguely* like OSNAP east and OSNAP west, except I don't think those sum to produce the total overturning. And Ekman could be part of a layer transport but here is has no depth reference. Gulf Stream has longitude bounds and a single latitude (``LATITUDE``, ``LONGITUDE_BOUND``) and limits over which the depths are represented (``DEPTH_BOUND``?) but no N_LEVELS. It doesn't quite make sense to call the dimension N_PROF since these aren't profiles. Maybe **N_COMPONENT**?

Summary of FW2015 files:
~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``MOCproxy_for_figshare_v1.mat``

  - ``TIME``: dimension ``TIME`` (264,), type datetime

  - ``MOC_PROXY``: dimension ``TIME``, units `Sv`

  - ``EK``: dimension ``TIME``, units `Sv`

  - ``GS``: dimension ``TIME``, units `Sv`

  - ``UMO_PROXY``: dimension ``TIME``, units `Sv`

Potential reformats:
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Overturning:**

  - ``MOC``: time series (dimension: ``TIME``)

- **Component transports:**

  - Dimensions: ``TIME``, ``N_COMPONENT`` (1404, 7)

  - Coordinates: ``LATITUDE``, ``LONGITUDE_BOUNDS`` (scalar, x2), ``TIME`` in datetime. ``N_COMPONENT`` for the number of components.

  - Variables: ``TRANSPORT`` (``TIME``, ``N_COMPONENT``) - This would also have ``TRANSPORT_NAME`` (``N_COMPONENT``, string) to indicate what the component is (e.g. `EK`, `GS`, `LNADW`, `MOC`, `MOC_PROXY`, `UMO_GRID`, `UMO_PROXY`, `UNADW_GRID`, etc). Note that some of these were just copies of what the RAPID time series was at the time.