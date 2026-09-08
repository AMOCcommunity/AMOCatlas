About AMOCatlas
===============

**What is this?**

AMOCatlas is a Python package for loading data on the Atlantic Meridional Overturning Circulation (AMOC), from both in-situ observing arrays and blended or estimated products. It gives you a single way to access data from different programmes around the Atlantic.

**Why AMOC?**

The Atlantic Meridional Overturning Circulation moves warm water north and cold water south in the Atlantic Ocean. It's important for climate - think of it as a giant conveyor belt that helps regulate temperatures in Europe and beyond.

Scientists monitor this circulation at several locations using moorings and other instruments. AMOCatlas makes it easier to work with data from these monitoring arrays.

**What data sources are included?**

AMOCatlas serves two kinds of source. *Observing arrays* are direct in-situ measurements from moored instruments; *blended/estimated products* derive transports from satellite altimetry, Argo, XBT, or statistical methods. Both are loaded through the same ``read.<name>()`` interface.

*Observing arrays (in-situ):*

* **RAPID (26°N)** - The longest-running basin-wide array, monitoring since 2004
* **MOCHA (26°N)** - Meridional heat transport, measured alongside RAPID since 2004
* **MOVE (16°N)** - Tropical Atlantic monitoring, west of the Mid-Atlantic Ridge
* **OSNAP (Subpolar North Atlantic)** - Overturning in the subpolar North Atlantic
* **SAMBA (34.5°S)** - South Atlantic monitoring
* **DSO (Denmark Strait)** - Denmark Strait overflow transport
* **FBC (Faroe Bank Channel)** - Faroe Bank Channel overflow transport
* **Arctic Gateway** - Pan-Arctic gateway transports

*Blended / estimated products:*

* **NOAC (47°N)** - North Atlantic Current MOC
* **41°N** - Meridional overturning from Argo floats and altimetry
* **FW2015 (26°N)** - Satellite altimetry and cable-based transport estimates
* **SF2021 (26°N)** - Overturning estimate from satellite altimetry
* **NAC** - North Atlantic Current from satellite and float observations
* **CALAFAT2025** - Bayesian estimates of Atlantic meridional heat transport
* **ZHENG2024** - Observation-based Atlantic meridional freshwater transport
* **LEBRAS35N (35°N)** - Overturning from deep moorings, floats, and satellite altimetry
* **AXMOC34.5S** - Estimates of AMOC, heat and freshwater transports at 34.5°S
* **AXMOC22.5S** - Estimates of AMOC and heat transport at 22.5°S

**What can you do with it?**

* Load data from any of these sources with just a few lines of code
* Compare data across different locations
* Make plots with consistent styling
* Access both raw datasets (with original variable names) and standardised datasets (for ease of use between different sources).
* Get logs of what data was downloaded and processed

The package handles downloading, caching, and organizing the data so you can focus on the science.  Note that if the web-based locations of the original datasets change, that links may break.  Please then raise an issue (see below) or try a fix yourself (see developer guide).

Installation
============

**Quick Install**

To install the latest released version from PyPI:

.. code-block:: bash

    python -m pip install amocatlas

This allows you to import the package into a Python file or notebook with:

.. code-block:: python

    import amocatlas

**Install for Contributing**

To install a local, development version for contributing, clone the repository and run:

.. code-block:: bash

    git clone https://github.com/AMOCcommunity/amocatlas.git
    cd amocatlas
    pip install -e ".[dev]"

This installs ``amocatlas`` locally. The ``-e`` ensures that any edits you make in the files will be picked up by scripts that import functions from ``amocatlas``. The ``[dev]`` extra pulls in the additional Python packages needed for development, including building documentation, running tests, and code linting.

You can run the example Jupyter notebook by launching JupyterLab with ``jupyter-lab`` and navigating to the ``notebooks`` directory, or in VS Code or other Python GUI.

**Testing**

All new functions should include tests. You can run tests locally and generate a coverage report with:

.. code-block:: bash

    pytest --cov=amocatlas --cov-report term-missing tests/

This shows what lines of a module (e.g., ``amocatlas/read.py``) are not covered by existing tests (located in ``tests/``). Try to ensure that all lines of your contribution are covered in the tests.

See also the `Developers Guide <developer_guide.html>`_ for coding conventions, automatic GitHub Actions triggered on pull requests, and example Git workflows.

Getting Started
===============

The quickest way to try it out:

.. code-block:: python

    from amocatlas import read

    # Load standardized data ready for analysis
    ds = read.rapid()
    print(ds)

Check out the demo notebook for more examples.

**Need help?**

* Full documentation: https://amoccommunity.github.io/amocatlas
* Issues and questions: https://github.com/AMOCcommunity/amocatlas/issues
* Contributing: See our developer guide

.. note::
    This work has been carried out within the framework of the `EPOC project <http://epoc-eu.org>`_ funded by the European Union's Horizon Europe programme (grant agreement No 101059547), under call HORIZON-CL6-2021-CLIMATE01. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them.
   