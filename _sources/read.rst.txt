read module
===========

.. currentmodule:: amocatlas.read

The intuitive API for AMOCatlas (v0.2.0+). Returns standardized, analysis-ready data by default.

Key Features
------------

- **Standardized by default**: Consistent variable names, metadata, and units following oceanographic conventions
- **Single dataset return**: Returns one dataset by default (most common use case)
- **IDE-friendly**: Autocompletion support for array names and parameters  
- **Flexible**: Use ``raw=True`` to get data in original file formats when needed

Quick Examples
--------------

Basic usage (recommended)::

    from amocatlas import read
    
    # Get standardized, analysis-ready data
    rapid_data = read.rapid()                    # Single dataset
    osnap_data = read.osnap(version="2025")      # Version parameter
    
    # Get all files for power users
    all_rapid = read.rapid(all_files=True)       # List of datasets
    
    # Get raw data when needed
    raw_data = read.rapid(raw=True)              # Original format

Available Array Functions
-------------------------

.. autofunction:: rapid
.. autofunction:: move  
.. autofunction:: osnap
.. autofunction:: samba
.. autofunction:: arcticgateway
.. autofunction:: fw2015
.. autofunction:: mocha
.. autofunction:: wh41n
.. autofunction:: dso  
.. autofunction:: noac47n
.. autofunction:: fbc
.. autofunction:: calafat2025
.. autofunction:: zheng2024
.. autofunction:: nac
.. autofunction:: sf2021
.. autofunction:: lebras35n
.. autofunction:: axmoc22s
.. autofunction:: axmoc34s