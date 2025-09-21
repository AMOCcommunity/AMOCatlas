.. This file is included under 'format_orig.rst' and should use '~~' or lower as the top header level.

.. _array-move:

MOVE Original Data Format
-------------------------

MOVE provides the TRANSPORT_TOTAL which corresponds to the MOC, but also things like transport_component_internal (``TIME``,), transport_component_internal_offset (``TIME``,), and transport_component_boundary (``TIME``,).  This would be similar to RAPID's version of "interior transport" and "western boundary wedge", but it's not so clear how to make these similarly named.

OS_MOVE_TRANSPORTS.nc
~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Variables
   :widths: 12 22 14 10 70
   :header-rows: 1

   * - Name
     - Dimensions
     - Shape
     - Units
     - Description
   * - ``TIME``
     - ``TIME``
     - (6756,)
     - datetime
     -
       - **type**: datetime
       - **time coverage**: 2000-01-01 to 2018-06-30
   * - ``TRANSPORT_TOTAL``
     - ``TIME``
     - (6756,)
     - Sverdrup
     -
       - **standard_name**: ``ocean_volume_transport_across_line``
       - **long_name**: Total ocean volume transport across the MOVE line between Guadeloupe and Researcher Ridge in the depth layer defined by pressures 1200 to 4950 dbar
       - **valid_min**: -100.0
       - **valid_max**: 100.0
   * - ``transport_component_internal``
     - ``TIME``
     - (6756,)
     - Sverdrup
     -
       - **long_name**: Internal component of ocean volume transport across the MOVE line
       - **valid_min**: -100.0
       - **valid_max**: 100.0
   * - ``transport_component_internal_offset``
     - ``TIME``
     - (6756,)
     - Sverdrup
     -
       - **long_name**: Offset to be added to internal component of ocean volume transport across the MOVE line
       - **valid_min**: -100.0
       - **valid_max**: 100.0
   * - ``transport_component_boundary``
     - ``TIME``
     - (6756,)
     - Sverdrup
     -
       - **long_name**: Boundary component of ocean volume transport across the MOVE line
       - **valid_min**: -100.0
       - **valid_max**: 100.0
