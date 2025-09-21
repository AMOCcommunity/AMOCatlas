.. This file is included under 'format_orig.rst' and should use '~~' or lower as the top header level.

.. _array-41n:

41°N Original Data Format
-------------------------

The 41°N array provides AMOC estimates derived from Argo float observations and satellite altimetry data, extending the observational record back to 2002.

.. note::
   **Documentation stub**: This section needs to be completed with detailed format specifications.
   
   See GitHub issue for 41°N data format documentation.

hobbs_willis_amoc41N_tseries.txt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This dataset contains monthly time series of AMOC transport estimates at 41°N.

.. list-table:: Variables (preliminary)
   :widths: 12 22 14 10 35
   :header-rows: 1

   * - Name
     - Dimensions
     - Shape
     - Units
     - Description
   * - ``TIME``
     - ``TIME``
     - (TBD,)
     - datetime
     - Time coordinate
   * - ``EKMAN``
     - ``TIME``
     - (TBD,)
     - Sv
     - Ekman volume transport
   * - ``V_GEOS``
     - ``TIME``
     - (TBD,)
     - Sv
     - Northward geostrophic transport
   * - ``MOT``
     - ``TIME``
     - (TBD,)
     - Sv
     - Meridional overturning volume transport
   * - ``MOHT``
     - ``TIME``
     - (TBD,)
     - PW
     - Meridional overturning heat transport

.. todo::
   - Complete data format specifications
   - Add detailed variable descriptions
   - Document data processing methodology
   - Add references to Hobbs & Willis methodology