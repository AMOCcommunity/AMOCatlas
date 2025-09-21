
Controlled Vocabularies
============

This is an analysis of what vocabularies might be useful for the AC1 datasets.

A primary reference vocabulary is the "Climate and Forecast (CF) Standard Names" vocabulary, which is a controlled vocabulary for climate and forecast data. The CF standard names are used to describe the physical variables in the datasets.  See [http://vocab.nerc.ac.uk/standard_name/](http://vocab.nerc.ac.uk/standard_name/).

We also have the SeaDataNet Parameter Discovery Vocabulary, which is a controlled vocabulary for oceanographic parameters. The SeaDataNet vocabulary is used to describe the parameters in the datasets. See [http://vocab.nerc.ac.uk/collection/P02/current/](http://vocab.nerc.ac.uk/collection/P02/current/).

Coordinates
-----------

latitude
~~~~~~~~

**Description**: Geographic latitude, positive northward.

- **CF Standard Name**: `latitude`
- **Suggested Units**: `degree_north`
- **Vocabulary**: [Insert NERC P07 Concept ID here]
- **Vocabulary (URI)**: [Insert URI here]
- **SeaDataNet Parameter**: [Optional — insert if applicable]
- **CMIP6 Variable Name**: `lat`
- **Notes**:
  - Used for geographic coordinates in regular and curvilinear grids.
  - In rotated grids, use `grid_latitude` instead.

longitude
~~~~~~~~~

**Description**: Geographic longitude, positive eastward.

- **CF Standard Name**: `longitude`
- **Suggested Units**: `degree_east`
- **Vocabulary**: [Insert NERC P07 Concept ID here]
- **Vocabulary (URI)**: [Insert URI here]
- **SeaDataNet Parameter**: [Optional — insert if applicable]
- **CMIP6 Variable Name**: `lon`
- **Notes**:
  - Used for geographic coordinates in regular and curvilinear grids.
  - In rotated grids, use `grid_longitude` instead.


Temperature
-----------

**SeaDataNet Parameter Discovery Vocabulary (P02):**

- **Code:** TEMP — Temperature of the water column

- **URI:** https://vocab.nerc.ac.uk/collection/P02/current/TEMP/

- **Definition:** Includes temperature parameters at any depth in the water column (excluding the top few microns sampled by radiometers), encompassing both measured and calculated values like Conservative Temperature.


sea_water_conservative_temperature (CT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Conservative Temperature following TEOS-10.

- **CF Standard Name**: `sea_water_conservative_temperature`
- **Suggested Units**: `degree_Celsius`
- **Vocabulary**: NERC P07 Concept ID IFEDAFIE
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/IFEDAFIE/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: similar to `thetao`
- **Definition:** Conservative Temperature is defined as part of the Thermodynamic Equation of Seawater 2010 (TEOS-10), and represents specific potential enthalpy divided by a fixed heat capacity value. It is a more accurate proxy for ocean heat content than potential temperature.
- **Notes**:
  - Recommended for TEOS-10 compliance.
  - Derived from in-situ T, S, and P in most observational datasets.
  - Conservative Temperature is TEOS-10’s recommended replacement for potential temperature in climate-quality datasets.

sea_water_temperature (TEMP)
~~~~~~~~~~~~~~~~~~~~~

**Description**: In-situ (measured) temperature of seawater.

- **CF Standard Name**: `sea_water_temperature`
- **Suggested Units**: `degree_Celsius`
- **Vocabulary**: NERC P07 Concept ID CFSN0335
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/CFSN0335/
- **SeaDataNet Parameter**: https://vocab.nerc.ac.uk/collection/P02/current/TEMP/
- **CMIP6 Variable Name**: similar to `thetao`
- **Definition:** The in situ temperature of sea water. This is the temperature a water parcel has at the location and depth of observation. To specify the depth, use a vertical coordinate variable.
- **Notes**:
  - `sea_water_temperature` is commonly used for directly measured CTD temperatures and numerical model outputs.
  - When using historical data, be mindful of the temperature scale (IPTS-68, ITS-90, etc.).
  - It is strongly recommended that a variable with this standard name should have a units_metadata attribute, with one of the values "on-scale" or "difference", whichever is appropriate for the data, because it is essential to know whether the temperature is on-scale (meaning relative to the origin of the scale indicated by the units) or refers to temperature differences (implying that the origin of the temperature scale is irrevelant), in order to convert the units correctly (cf. https://cfconventions.org/cf-conventions/cf-conventions.html#temperature-units).

sea_water_potential_temperature (POTEMP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Potential temperature referenced to the surface (0 dbar).

- **CF Standard Name**: `sea_water_potential_temperature`
- **Suggested Units**: `degree_Celsius`
- **Vocabulary**: NERC P07 Concept ID CFSN0329
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/CFSN0329/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: similar to `thetao`
- **Notes**:
  - Used where Conservative Temperature isn't available.
  - Not equivalent to in-situ temperature.


Salinity
--------

**SeaDataNet Parameter Discovery Vocabulary (P02):**

- **Code:** PSAL — Salinity of the water column

- **URI:** https://vocab.nerc.ac.uk/collection/P02/current/PSAL/

- **Definition:** Parameters quantifying the concentration of sodium chloride in any body of water at any point between the bed and the atmosphere



sea_water_absolute_salinity (SA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Absolute Salinity as defined in TEOS-10.

- **CF Standard Name**: `sea_water_absolute_salinity`
- **Suggested Units**: `g kg-1`
- **Vocabulary**: NERC P07 Concept ID JIBGDIEJ
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/JIBGDIEJ/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: Not typically used (models output practical salinity)
- **Definition:** Absolute Salinity, defined by TEOS-10, is the mass fraction of dissolved material in sea water. It is the salinity variable that yields the correct in situ density using the TEOS-10 equation of state, even when composition differs from the Reference Composition.
- **Notes**:
  - Often computed from Practical Salinity using regional climatologies of the Absolute Salinity Anomaly.
  - Required for accurate density and heat content calculations under TEOS-10.
  - Required for calculating Conservative Temperature and density under TEOS-10.

sea_water_practical_salinity (PSAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Practical Salinity calculated from conductivity, temperature, and pressure.

- **CF Standard Name**: `sea_water_practical_salinity`
- **Suggested Units**: unitless (PSS-78)
- **Vocabulary**: NERC P07 Concept ID IADIHDIJ
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/IADIHDIJ/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: `so`
- **Definition:** Practical Salinity (S_P) is derived from conductivity measurements and expressed on the Practical Salinity Scale of 1978 (PSS-78). It is dimensionless and does not represent mass concentration.
- **Notes**:
  - This is the most commonly archived salinity value in observational datasets since 1978.
  - Should not be used for pre-1978 datasets or when salinity is determined via chlorinity.
  - Should be converted to Absolute Salinity for TEOS-10 consistency.

sea_water_salinity (SALIN)
~~~~~~~~~~~~~~~~~~

**Description**: Generic salinity (unspecified type — practical, absolute, etc.).

- **CF Standard Name**: `sea_water_salinity`
- **Suggested Units**: unitless or `g kg-1` depending on context
- **Vocabulary**: NERC P07 Concept ID CFSN0331
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/CFSN0331/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: sometimes `so`
- **Definition:** A general term for the salt content of sea water, not tied to a specific measurement scale (e.g., PSS-78). Use only when the salinity type is unknown or does not conform to a defined standard.
- **Notes**:
  - Use of this standard name is **discouraged** for post-1978 data when `sea_water_practical_salinity` is applicable
  - May appear in legacy datasets or when the methodology is uncertain.
  - Prefer `sea_water_absolute_salinity` or `sea_water_practical_salinity` where possible.


Pressure
--------



sea_water_pressure (PRES)
~~~~~~~~~~~~~~~~~~

**Description**: Pressure in the water column relative to the sea surface.

- **CF Standard Name**: `sea_water_pressure`
- **Suggested Units**: `dbar`
- **Vocabulary**: NERC P07 Concept ID CFSN0330
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/CFSN0330/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: Not typically output
- **Notes**:
  - Often derived from depth using standard formulas or pressure sensor readings.
  - Needed for TEOS-10 calculations and vertical gridding.

sea_water_pressure_at_sea_floor (BOTPRES)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Pressure at the seafloor; equivalent to full water column weight.

- **CF Standard Name**: `sea_water_pressure_at_sea_floor`
- **Suggested Units**: `dbar`
- **Vocabulary**: NERC P07 Concept ID CF12N583
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CF12N583/
- **SeaDataNet Parameter**: Not listed in https://vocab.seadatanet.org/v_bodc_vocab_v2/search.asp?lib=P02
- **CMIP6 Variable Name**: Not commonly used
- **Notes**:
  - Common output from bottom pressure recorders (BPRs).
  - Useful for estimating barotropic transport variability.

reference_pressure (REFPRES)
~~~~~~~~~~~~~~~~~~

**Description**: A constant scalar pressure value used to define the reference state for potential temperature or density calculations.

- **CF Standard Name**: `reference_pressure`
- **Suggested Units**: `Pa` or `dbar`
- **Vocabulary**: NERC P07 Concept ID 9334Z59K
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/9334Z59K/
- **SeaDataNet Parameter**: Not listed
- **CMIP6 Variable Name**: Not applicable
- **Notes**:
  - Required as a scalar coordinate in CF-compliant potential temperature or density fields.
  - Units are usually in pascals (Pa) for CF, but `dbar` is commonly used in oceanography for readability.


Density
-------

**SeaDataNet Parameter Discovery Vocabulary (P02):**

- **Code:** DENS — Density of the water column
- **URI:** http://vocab.nerc.ac.uk/collection/P02/current/SIGT/
- **Definition:** Absolute determinations of water column density plus parameters (generally expressed as density anomaly) derived from temperature and salinity

sea_water_sigma_theta (SIGMA)
~~~~~~~~~~~~~~~~~~~~~

**Description**: Potential density anomaly (sigma-theta), referenced to 0 dbar.

- **CF Standard Name**: `sea_water_sigma_theta`
- **Suggested Units**: `kg m-3` (anomaly: subtract 1000 from density)
- **Vocabulary**: NERC P07 Concept ID CFSN0333
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0333/
- **SeaDataNet Parameter**: See P02 DENS
- **CMIP6 Variable Name**: Not applicable
- **Definition:** Potential density of sea water (density when moved adiabatically to a reference pressure), minus 1000 kg m⁻³. Commonly used to identify isopycnal surfaces. Reference pressure should be specified via a scalar coordinate with standard name `reference_pressure`.
- **Notes**:
  - The sigma-theta value is dimensionally equivalent to density minus 1000.
  - Reference pressure should be specified via `reference_pressure`.

sea_water_potential_density
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Potential density referenced to sea surface (or other scalar pressure).

- **CF Standard Name**: `sea_water_potential_density`
- **Suggested Units**: `kg m-3`
- **Vocabulary**: NERC P07 Concept ID CFSN0395
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0395/
- **SeaDataNet Parameter**: See P02 DENS
- **CMIP6 Variable Name**: Not typically used
- **Definition:** The density a seawater parcel would have if moved adiabatically to a reference pressure, usually sea level pressure. Reference pressure should be specified using a `reference_pressure` scalar coordinate.
- **Notes**:
    - Subtract 1000 kg m⁻³ to obtain `sigma_theta`.
    - Reference pressure must be declared as a scalar coordinate.

sea_water_neutral_density (GAMMA_N)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Neutral density following the neutral tangent plane.

- **CF Standard Name**: `sea_water_neutral_density`
- **Suggested Units**: `kg m-3`
- **Vocabulary**: NERC P07 Concept ID BBAH2105
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/BBAH2105/
- **SeaDataNet Parameter**: See P02 DENS
- **CMIP6 Variable Name**: `gamma_n`
- **Definition:** Neutral density is a variable whose surfaces approximately follow the direction of no buoyant motion. Designed to represent the neutral tangent plane slope more closely than potential density.
- **Notes**:
  - Follows slope of neutral tangent plane more closely than potential density.
  - See Jackett & McDougall (1997) for reference formulation.


ocean_sigma_coordinate
~~~~~~~~~~~~~~~~~~~~~~

**Description**: Parametric vertical coordinate used in terrain-following models.

- **CF Standard Name**: `ocean_sigma_coordinate`
- **Suggested Units**: unitless (coordinate index)
- **Vocabulary**: NERC P07 Concept ID CFSN0473
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0473/
- **SeaDataNet Parameter**: Not listed
- **CMIP6 Variable Name**: Not applicable
- **Definition:** A parametric vertical coordinate used primarily in terrain-following ocean models. Not to be confused with `sea_water_sigma_theta`, which is a density-related scalar field.
- **Notes**:
    - Typically defined by formulas relating model levels to depth using pressure, surface elevation, and  bottom depth.
    - Not equivalent to `sea_water_sigma_theta`.
    - See CF Conventions Appendix D for formula terms and guidance.

ocean_sigma_z_coordinate
~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Hybrid sigma-z coordinate accounting for vertical stretching/compression.

- **CF Standard Name**: `ocean_sigma_z_coordinate`
- **Suggested Units**: unitless (coordinate index)
- **Vocabulary**: NERC P07 Concept ID 3HWMM33G
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/3HWMM33G/
- **SeaDataNet Parameter**: Not listed
- **CMIP6 Variable Name**: Not applicable
- **Definition:** A variant of the sigma coordinate system that adjusts for local stretching/compression in the vertical axis (z-star or z-level hybrid coordinates). See Appendix D of the CF convention for information about parametric vertical coordinates.
- **Notes**:
  - Used in ocean models employing z-star or hybrid vertical grids.
  - See CF Conventions Appendix D for coordinate formulation.



Velocity
--------

**SeaDataNet Parameter Discovery Vocabulary (P02):**

- **Code:** RFVL — Horizontal velocity of the water column (currents)
- **URI:** https://vocab.nerc.ac.uk/collection/P02/current/RFVL/
- **Definition:** Parameters expressing the velocity (including scalar speeds and directions) of water column horizontal movement, commonly termed Eulerian currents

baroclinic_northward_sea_water_velocity (VVEL_REL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Northward component of the baroclinic velocity field.

- **CF Standard Name**: `baroclinic_northward_sea_water_velocity`
- **Suggested Units**: `m s-1`
- **Vocabulary**: NERC P07 Concept ID CFSN0729
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0729/
- **SeaDataNet Parameter**: See P02 RFVL
- **CMIP6 Variable Name**: Not applicable
- **Definition:** The northward component of the baroclinic part of the sea water velocity field. "Baroclinic" refers to the component of motion associated with density gradients (excluding the depth-averaged flow).
- **Notes**:
  - Refers to the shear flow due to density stratification.
  - Computed as full velocity minus barotropic (depth-mean) component.

barotropic_northward_sea_water_velocity (VVEL_BARO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Depth-averaged northward sea water velocity (barotropic component).

- **CF Standard Name**: `barotropic_northward_sea_water_velocity`
- **Suggested Units**: `m s-1`
- **Vocabulary**: NERC P07 Concept ID CFSN0731
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0731/
- **SeaDataNet Parameter**: See P02 RFVL
- **CMIP6 Variable Name**: Not applicable
- **Definition:** The northward component of the depth-averaged sea water velocity. "Barotropic" denotes the vertically uniform component of flow.
- **Notes**:
  - Represents vertically uniform component of flow.
  - Important for basin-scale transport diagnostics and section-integrated flow estimates.



Transport
---------

ocean_volume_transport_across_line (TRANSPORT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Volume transport across a specified line (e.g., a latitude section).

- **CF Standard Name**: `ocean_volume_transport_across_line`
- **Suggested Units**: `m3 s-1`
- **Vocabulary**: NERC P07 Concept ID W946809H
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/W946809H/
- **SeaDataNet Parameter**: [Insert if applicable]
- **CMIP6 Variable Name**: [Optional]
- **Notes**:
  - Represents the integral of normal velocity across a line or section.
  - Useful in mooring and model diagnostics.

ocean_meridional_overturning_streamfunction (MOC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Net vertical and meridional circulation of the ocean, excluding parameterized eddy components.

- **CF Standard Name**: `ocean_meridional_overturning_streamfunction`
- **Suggested Units**: `m3 s-1`
- **Vocabulary**: NERC P07 Concept ID CFSN0466
- **Vocabulary (URI)**: https://vocab.nerc.ac.uk/collection/P07/current/CFSN0466/
- **SeaDataNet Parameter**: Not available
- **CMIP6 Variable Name**: `msftmz` or similar
- **Notes**:
  - Derived from zonally integrated meridional velocity.
  - Distinct from `ocean_meridional_overturning_mass_streamfunction`, which includes all processes (resolved and parameterized).
  - Used in MOC diagnostics from models and arrays like RAPID, OSNAP.

ocean_meridional_overturning_mass_streamfunction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Overturning streamfunction including all resolved and parameterized mass transport processes.

- **CF Standard Name**: `ocean_meridional_overturning_mass_streamfunction`
- **Suggested Units**: `kg s-1`
- **Vocabulary**: NERC P07 Concept ID CF12N554
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CF12N554/
- **SeaDataNet Parameter**: [Insert if applicable]
- **CMIP6 Variable Name**: `msftmm` or similar
- **Notes**:
  - Includes parameterized eddy transport.
  - Mass-based counterpart to volume streamfunction.



Freshwater Transport
--------------------

northward_ocean_freshwater_transport (FWT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Total northward transport of freshwater.

- **CF Standard Name**: `northward_ocean_freshwater_transport`
- **Suggested Units**: `m3 s-1` (often presented as Sverdrup freshwater equivalents)
- **Vocabulary**: NERC P07 Concept ID CFSN0507
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0507/
- **SeaDataNet Parameter**: Not available
- **CMIP6 Variable Name**: Not standardized
- **Definition:** Meridional overturning streamfunction representing the net vertical and meridional circulation of the ocean, excluding the contribution from parameterized eddy velocities. This streamfunction is typically derived from the zonal integration of the meridional component of velocity.
- **Notes**:
  - Includes contributions from overturning, gyre, and eddies.
  - Often derived from salinity and velocity sections or model integrations, expressed in Sverdrup equivalents adjusted for freshwater flux

northward_ocean_freshwater_transport_due_to_overturning (FWT_OV)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Freshwater transport component associated with the overturning circulation.

- **CF Standard Name**: `northward_ocean_freshwater_transport_due_to_overturning`
- **Suggested Units**: `m3 s-1` or `Sverdrup freshwater equivalent`
- **Vocabulary**: NERC P07 Concept ID CFSN0482
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0482/
- **SeaDataNet Parameter**: Not available
- **CMIP6 Variable Name**: Not standardized
- **Notes**:
  - Computed using zonal mean salinity and baroclinic velocity.
  - Used in freshwater budget decompositions of the MOC, for the component associated with the overturning.
  - Often expressed in Sverdrup equivalents adjusted for freshwater flux.

northward_ocean_freshwater_transport_due_to_gyre (FWT_GYRE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Component of freshwater transport from horizontal gyre-scale circulation.

- **CF Standard Name**: `northward_ocean_freshwater_transport_due_to_gyre`
- **Suggested Units**: `m3 s-1` or `Sverdrup freshwater equivalent`
- **Vocabulary**: NERC P07 Concept ID CFSN0510
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0510/
- **SeaDataNet Parameter**: Not available
- **CMIP6 Variable Name**: Not standardized
- **Notes**:
  - Computed using salinity and velocity anomalies relative to zonal mean.
  - Complements overturning and eddy components in MOC decomposition.

Heat Transport
--------------------


northward_ocean_heat_transport (MHT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Total northward heat transport by ocean, including seawater and sea ice.

- **CF Standard Name**: `northward_ocean_heat_transport`
- **Suggested Units**: `W`
- **Vocabulary**: NERC P07 Concept ID CFSN0483
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0483/
- **SeaDataNet Parameter**: [Insert if applicable]
- **CMIP6 Variable Name**: [Optional]
- **Notes**:
  - Integrates advective transport of heat across latitude lines.
  - Useful for large-scale energy budget diagnostics.

northward_ocean_heat_transport_due_to_gyre (MHT_GYRE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Heat transport component from horizontal gyre circulation.

- **CF Standard Name**: `northward_ocean_heat_transport_due_to_gyre`
- **Suggested Units**: `W`
- **Vocabulary**: NERC P07 Concept ID CFSN0486
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0486/
- **SeaDataNet Parameter**: [Insert if applicable]
- **CMIP6 Variable Name**: [Optional]
- **Notes**:
  - Derived from deviation of velocity and temperature from zonal means.
  - Excludes parameterized eddy contributions.

northward_ocean_heat_transport_due_to_overturning (MHT_OV)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Component of heat transport due to overturning circulation.

- **CF Standard Name**: `northward_ocean_heat_transport_due_to_overturning`
- **Suggested Units**: `W`
- **Vocabulary**: NERC P07 Concept ID CFSN0487
- **Vocabulary (URI)**: http://vocab.nerc.ac.uk/collection/P07/current/CFSN0487/
- **SeaDataNet Parameter**: [Insert if applicable]
- **CMIP6 Variable Name**: [Optional]
- **Notes**:
  - Computed from zonal mean profiles.
  - Excludes eddy and gyre components.
