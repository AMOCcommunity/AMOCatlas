About AMOCarray
===============

What is this?
-------------

AMOCarray is a Python package for loading data from Atlantic Meridional Overturning Circulation (AMOC) observing arrays. It gives you a simple way to access data from different programmes around the Atlantic.

Why AMOC?
---------

The Atlantic Meridional Overturning Circulation moves warm water north and cold water south in the Atlantic Ocean. It's important for climate - think of it as a giant conveyor belt that helps regulate temperatures in Europe and beyond.

Scientists monitor this circulation at several locations using moorings and other instruments. AMOCarray makes it easier to work with data from these monitoring arrays.

What arrays are included?
-------------------------

* **RAPID (26°N)** - The longest-running basin-wide array, monitoring since 2004
* **MOVE (16°N)** - Tropical Atlantic monitoring, west of the Mid-Atlantic Ridge
* **OSNAP (Subpolar)** - Covers the subpolar North Atlantic
* **SAMBA (34.5°S)** - South Atlantic monitoring
* **41°N** - Uses Argo float data and altimetry
* **DSO** - Denmark Strait overflow
* **RAPID/MOCHA** - Heat transport estimates from 26°N
* **FW2015** - Altimetry-based transport estimates at 26°N

What can you do with it?
------------------------

* Load data from any array of the above arrays (or measurement methods) with just a few lines of code
* Compare data across different locations
* Make plots with consistent styling
* Access both sample datasets (for testing) and full datasets
* Get detailed logs of what data was downloaded and processed

The package handles downloading, caching, and organizing the data so you can focus on the science.  Note that if the web-based locations of the original datasets change, that links may break.  Please then raise an issue (see below) or try a fix yourself (see developer guide).

Getting started
---------------

The quickest way to try it out::

    from amocarray import readers

    # Load a sample dataset
    ds = readers.load_sample_dataset("rapid")
    print(ds)

Check out the demo notebook for more examples.

Need help?
----------

* Full documentation: https://amoccommunity.github.io/amocarray
* Issues and questions: https://github.com/AMOCcommunity/amocarray/issues
* Contributing: See our developer guide

.. note::
   This project is supported by the Horizon Europe project EPOC - Explaining and Predicting the Ocean Conveyor.
