
Units Reference: for AC1
=============================

This document summarizes unit definitions relevant to the `amocarray` project, based on `udunits2-base.xml`.


Check out `udunits <https://docs.unidata.ucar.edu/udunits/current/>`_.

SI base units (XML) are `here <https://docs.unidata.ucar.edu/udunits/current/udunits2-base.xml>`_.

Derived units (XML) are `here <https://docs.unidata.ucar.edu/udunits/current/udunits2-derived.xml>`_.

Non-SI units including Sverdrup (full spelling used to avoid confusion with "Sv" for sievert in the SI unit system).


Variables
---------

Mass/Volume Units
~~~~~~~~~~~~~~~~~

+--------------------------+---------------+------------------+
| Name                     | Symbol        | Definition       |
+==========================+===============+==================+
| gram_per_cubic_meter     | g/m³,         | 0.001 kg/m³      |
|                          | g m-3         |                  |
+--------------------------+---------------+------------------+
| kilogram_per_cubic_meter | kg/m³,        | base SI unit     |
|                          | **kg m-3**    |                  |
+--------------------------+---------------+------------------+

Length Units
~~~~~~~~~~~~~~~~~

+-----------+------------+----------------+
| Name      | Symbol     | Definition     |
+===========+============+================+
| meter     | **m**      | base SI unit   |
+-----------+------------+----------------+
| centimeter| cm         | 0.01 m         |
+-----------+------------+----------------+
| kilometer | km         | 1000 m         |
+-----------+------------+----------------+

Temperature Units
~~~~~~~~~~~~~~~~~

+------------------+---------------+-----------------------------+
| Name             | Symbol        | Definition                  |
+==================+===============+=============================+
| degree_Celsius   | °C,           | 1 K offset by -273.15       |
|                  | **Celsius**   |                             |
+------------------+---------------+-----------------------------+
| kelvin           | K             | base SI unit                |
+------------------+---------------+-----------------------------+

Conductivity Units
~~~~~~~~~~~~~~~~~

+-----------------------------+-----------+-------------------+
| Name                        | Symbol    | Definition        |
+=============================+===========+===================+
| siemens_per_meter           | S/m,      | base SI unit      |
|                             | **S m-1** |                   |
+-----------------------------+-----------+-------------------+
| millisiemens_per_centimeter | mS/cm     | 0.1 S/m           |
+-----------------------------+-----------+-------------------+


Pressure Units
~~~~~~~~~~~~~~~~~

+------------+------------+----------------------+
| Name       | Symbol     | Definition           |
+============+============+======================+
| decibar    | **dbar**   | 10,000 Pa            |
+------------+------------+----------------------+
| kilopascal | kPa        | 1,000 Pa             |
+------------+------------+----------------------+
| pascal     | Pa         | base SI pressure     |
+------------+------------+----------------------+
| bar        | bar        | 100,000 Pa           |
+------------+------------+----------------------+


Velocity Units
~~~~~~~~~~~~~~~~~



+------------------------+-----------+----------------+
| Name                   | Symbol    | Definition     |
+========================+===========+================+
| centimeter_per_second  | cm/s,     | 0.01 m/s       |
|                        | cm s-1    |                |
+------------------------+-----------+----------------+
| meter_per_second       | m/s,      | base SI unit   |
|                        | **m s-1** |                |
+------------------------+-----------+----------------+








Angle Units (Accepted Non-SI)
~~~~~~~~~~~~~~~~~

These units are accepted for use with SI and commonly used in geophysical data.

+-------------+-------------+--------------------------+
| Name        | Symbol      | Conversion to radians    |
+=============+=============+==========================+
| degree      | °,          | π / 180                  |
|             | **degrees** |                          |
+-------------+-------------+--------------------------+
| arcminute   | ′           | (1/60) degree            |
+-------------+-------------+--------------------------+
| arcsecond   | ″           | (1/60) arcminute         |
+-------------+-------------+--------------------------+

Notes:
- Degrees are commonly used for geographic coordinates (latitude and longitude).
- These are dimensionless units in the SI sense but critical for interpreting spatial data.



Transport Units
~~~~~~~~~~~~~~~~~

+-------------------------+------------+-----------------------------+
| Name                    | Symbol     | Definition                  |
+=========================+============+=============================+
| **Sverdrup**            | Sverdrup   | 1e6 m³/s                    |
|                         |            | (full spelling preferred)   |
+-------------------------+------------+-----------------------------+
| cubic_meter_per_second  | m³/s,      | Ocean volume transport      |
|                         | **m3 s-1** |                             |
+-------------------------+------------+-----------------------------+

Energy and Power Units
~~~~~~~~~~~~~~~~~

+-----------+--------+--------------------------+
| Name      | Symbol | Definition               |
+===========+========+==========================+
| watt      | W      | J/s = kg·m²/s³           |
+-----------+--------+--------------------------+
| kilowatt  | kW     | 1000 W                   |
+-----------+--------+--------------------------+
| megawatt  | MW     | 1e6 W                    |
+-----------+--------+--------------------------+
| petawatt  | **PW** | 1e15 W                   |
+-----------+--------+--------------------------+
| joule     | J      | N·m = kg·m²/s²           |
+-----------+--------+--------------------------+


+--------------+--------+-------------------------+
| Name         | Symbol | Definition              |
+==============+========+=========================+
| kilojoule    | kJ     | 1000 J                  |
+--------------+--------+-------------------------+
| gigajoule    | GJ     | 1e9 J                   |
+--------------+--------+-------------------------+

Surface Heat Flux Units
~~~~~~~~~~~~~~~~~

+--------------------------+------------+------------------------------+
| Name                     | Symbol     | Definition                   |
+==========================+============+==============================+
| watt_per_square_meter    | W/m²,      | Heat flux density            |
|                          | **W m-2**  |                              |
+--------------------------+------------+------------------------------+




Mapping of Custom Conversions
-----------------------------

+------------------+------------------+------------------+--------------------------+
| Original Unit    | Canonical Unit   | Factor           | Notes                    |
+==================+==================+==================+==========================+
| cm/s, cm s-1     | m s-1            | 0.01             | Velocity                 |
+------------------+------------------+------------------+--------------------------+
| S/m              | mS cm-1          | 0.1              | Conductivity             |
+------------------+------------------+------------------+--------------------------+
| dbar             | Pa, kPa          | 10000, 10        | Pressure                 |
+------------------+------------------+------------------+--------------------------+
| degrees_Celsius  | Celsius          | 1                | Temperature              |
+------------------+------------------+------------------+--------------------------+
| m                | cm, km           | 100, 0.001       | Length                   |
+------------------+------------------+------------------+--------------------------+
| g m-3            | kg m-3           | 0.001            | Density                  |
+------------------+------------------+------------------+--------------------------+
| Sverdrup         | Sverdrup         | 1                | Transport                |
+------------------+------------------+------------------+--------------------------+
| W, J             | watt, joule      | base units       | Energy and Power         |
+------------------+------------------+------------------+--------------------------+

**Note:** Full "Sverdrup" spelling used to avoid confusion with "Sv" (sievert).


SI Unit Prefixes
------------------

Standard prefixes supported by UDUNITS-2 for scaling base and derived units.

+-----------+---------+--------------+
| Prefix    | Symbol  | Factor       |
+===========+=========+==============+
| yotta     | Y       | 1e24         |
| zetta     | Z       | 1e21         |
| exa       | E       | 1e18         |
| peta      | P       | 1e15         |
| tera      | T       | 1e12         |
| giga      | G       | 1e9          |
| mega      | M       | 1e6          |
| kilo      | k       | 1e3          |
| hecto     | h       | 1e2          |
| deca      | da      | 1e1          |
| deci      | d       | 1e-1         |
| centi     | c       | 1e-2         |
| milli     | m       | 1e-3         |
| micro     | µ (u)   | 1e-6         |
| nano      | n       | 1e-9         |
| pico      | p       | 1e-12        |
| femto     | f       | 1e-15        |
| atto      | a       | 1e-18        |
| zepto     | z       | 1e-21        |
| yocto     | y       | 1e-24        |
+-----------+---------+--------------+

Notes:
- Prefixes can be applied to compatible base/derived units (e.g., kW, cm, µS/cm).
- `µ` is often typed as `u` in ASCII-only environments.
