.. This file is included under 'format_orig.rst' and should use '~~' or lower as the top header level.

.. _array-dso:

DSO Original Data Format
------------------------

The Denmark Strait Overflow (DSO) monitoring provides continuous time series of dense water overflow transport through Denmark Strait, a critical component of the Atlantic meridional overturning circulation.

.. note::
   **Documentation stub**: This section needs to be completed with detailed format specifications.
   
   See GitHub issue for DSO data format documentation.

DSO_transport_hourly_1996_2021.nc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This dataset contains hourly time series of Denmark Strait overflow transport from 1996 to 2021.

.. list-table:: Variables (preliminary)
   :widths: 12 22 14 10 35
   :header-rows: 1

   * - Name
     - Dimensions
     - Shape
     - Units
     - Description
   * - ``time``
     - ``time``
     - (TBD,)
     - datetime
     - Time coordinate (hourly)
   * - ``DSO``
     - ``time``
     - (TBD,)
     - Sv
     - Denmark Strait overflow volume transport

.. todo::
   - Complete data format specifications
   - Add detailed variable descriptions
   - Document overflow monitoring methodology
   - Add references to Hamburg/Reykjavik collaboration
   - Document quality control procedures
   - Add information about mooring array configuration