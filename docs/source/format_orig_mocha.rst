.. This file is included under 'format_orig.rst' and should use '~~' or lower as the top header level.

.. _array-mocha:

MOCHA Original Data Format
--------------------------

Summary of MOCHA files:
~~~~~~~~~~~~~~~~~~~~~~~~~~
The heat transports at RAPID-MOCHA are provided with N_LEVELS, TIME, and variables:

- Q_eddy

- Q_ek

- Q_fc

- Q_gyre

- Q_int.

Again, we have a situation where N_PROF isn't really appropriate. Maybe **N_COMPONENT**? WE should double check that things called **N_COMPONENT** then somehow sum to produce a total? Then we would have something like MHT_COMPONENTS (``N_COMPONENT``, ``TIME``) and MHT (``TIME``)

But we also have things like:

- T_basin (``TIME``, ``N_LEVELS``)

- T_basin_mean (``N_LEVELS``)

- T_fc_fwt (``TIME``)

- V_basin (``TIME``, ``N_LEVELS``) --> is this identical to new RAPID velo sxn?

- V_basin_mean (``N_LEVELS``)

- V_fc (``TIME``, ``N_LEVELS``)


Potential reformats:
~~~~~~~~~~~~~~~~~~~~~~~~~~

So this might be suggested as a TEMPERATURE (``TIME``, ``N_LEVELS``) but unclear how to indicate that this is a zonal mean temperature as compared to the ones which are TEMPERATURE (``N_PROF``, ``TIME``, ``N_LEVELS``) for the full sections.


- **Heat Transport Components**:

  - `Q_eddy`, `Q_ek`, `Q_fc`, `Q_gyre`, `Q_int` → suggest ``MHT_COMPONENT`` (``N_COMPONENT``, ``TIME``)

  - Total: ``MHT`` (``TIME``)

- **Additional Variables**:

  - `T_basin`, `V_basin`, `T_fc_fwt`, etc.

  - These suggest basin-mean properties: ``TEMPERATURE`` (``TIME``, ``N_LEVELS``)

- **Note**: ``N_COMPONENT`` should indicate summable components if applicable