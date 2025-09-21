Data Format Documentation Overview
===================================

This section contains documentation about data formats used in AMOCarray. The documentation is organized to follow the data processing workflow from native formats to standardized outputs.

Understanding the Documentation Structure
-----------------------------------------

The data format documentation is organized around four key stages of data handling:

.. list-table:: Documentation Organization
   :widths: 25 25 50
   :header-rows: 1

   * - Document
     - Purpose
     - When to Use
   * - :doc:`format_orig`
     - **Native formats** from observing arrays
     - Understanding original data structure from each array (RAPID, OSNAP, etc.)
   * - :doc:`format_oceanSITES`  
     - **Standards compliance** requirements
     - Implementing OceanSITES-compliant data formats
   * - :doc:`format_conversion`
     - **Conversion strategies** from native to standard
     - Planning how to transform native formats to standardized ones
   * - :doc:`format_AC1`
     - **Final standardized format** specification
     - Using ``amocarray.convert.to_AC1()`` function output

Workflow Overview
-----------------

The typical data processing workflow follows this sequence:

1. **Original Data** → Each observing array provides data in its own native format
2. **Analysis & Planning** → Understand native formats and plan conversions  
3. **Standardization** → Convert to OceanSITES-compliant intermediate format
4. **Final Output** → Produce AC1 standardized format for interoperability

.. code-block:: text

   Native Formats     Conversion       OceanSITES        AC1 Format
   (format_orig) →  (format_conversion) → (format_oceanSITES) → (format_AC1)
   
   RAPID.nc                                                    
   OSNAP.nc        →  Analysis &     →  Standards      →     Standardized
   MOVE.nc            Planning          Compliance            Output
   SAMBA.txt                                                  

Key Concepts
------------

**Array Independence**
   Each observing array (RAPID, OSNAP, MOVE, SAMBA, etc.) provides data in different formats, units, and structures. The native format documentation captures these differences.

**Standards Compliance**
   OceanSITES provides community standards for oceanographic data. We follow these conventions while adapting them for AMOC array requirements.

**Unified Access**
   The AC1 format provides a consistent interface regardless of which array the data originally came from, enabling cross-array analysis and comparison.

**Metadata Preservation**
   Throughout the conversion process, we preserve attribution to original data providers and maintain full provenance tracking.

Getting Started
---------------

- **New to the project?** Start with :doc:`format_orig` to understand the data landscape
- **Implementing readers?** Use :doc:`format_conversion` for conversion strategies  
- **Need standards compliance?** Refer to :doc:`format_oceanSITES` for requirements
- **Using converted data?** See :doc:`format_AC1` for the final format specification

Questions and Contributions
----------------------------

If you have questions about data formats or want to contribute to format development:

- Check our `GitHub issues <https://github.com/AMOCcommunity/amocarray/issues>`_
- See the :doc:`developer_guide` for contribution guidelines
- Review existing format documentation for similar arrays before proposing new formats