data_sources package
====================

.. currentmodule:: amocatlas.data_sources

Individual data source readers for each AMOC observing array and dataset.

Package Overview
----------------

Each module provides a read function for accessing its specific data source with consistent interfaces and error handling.

Module naming convention:
- Arrays include latitude: rapid26n, move16n, osnap55n, samba34s
- Special locations: wh41n (Willis & Hobbs), noac47n (North Atlantic Ocean Current) 
- Datasets by author/year: fw2015, calafat2025, zheng2024
- Overflow locations: dso (Denmark Strait), fbc (Faroe Bank Channel)

Available Functions
-------------------

.. autofunction:: read_rapid
.. autofunction:: read_move
.. autofunction:: read_osnap
.. autofunction:: read_osnap_2025
.. autofunction:: read_samba
.. autofunction:: read_fw2015
.. autofunction:: read_mocha
.. autofunction:: read_arcticgateway
.. autofunction:: read_dso
.. autofunction:: read_fbc
.. autofunction:: read_calafat2025
.. autofunction:: read_zheng2024
.. autofunction:: read_41n
.. autofunction:: read_47n
.. autofunction:: read_nac
.. autofunction:: read_sf2021
.. autofunction:: read_lebras35n
.. autofunction:: read_axmoc22s
.. autofunction:: read_axmoc34s

Submodules
----------

rapid26n
~~~~~~~~
.. automodule:: amocatlas.data_sources.rapid26n
   :members:
   :undoc-members:

move16n
~~~~~~~
.. automodule:: amocatlas.data_sources.move16n
   :members:
   :undoc-members:

osnap55n
~~~~~~~~
.. automodule:: amocatlas.data_sources.osnap55n
   :members:
   :undoc-members:

samba34s
~~~~~~~~
.. automodule:: amocatlas.data_sources.samba34s
   :members:
   :undoc-members:

arcticgateway
~~~~~~~~~~~~~
.. automodule:: amocatlas.data_sources.arcticgateway
   :members:
   :undoc-members:

fw2015
~~~~~~
.. automodule:: amocatlas.data_sources.fw2015
   :members:
   :undoc-members:

mocha26n
~~~~~~~~
.. automodule:: amocatlas.data_sources.mocha26n
   :members:
   :undoc-members:

wh41n
~~~~~
.. automodule:: amocatlas.data_sources.wh41n
   :members:
   :undoc-members:

dso
~~~
.. automodule:: amocatlas.data_sources.dso
   :members:
   :undoc-members:

noac47n
~~~~~~~
.. automodule:: amocatlas.data_sources.noac47n
   :members:
   :undoc-members:

fbc
~~~
.. automodule:: amocatlas.data_sources.fbc
   :members:
   :undoc-members:

calafat2025
~~~~~~~~~~~
.. automodule:: amocatlas.data_sources.calafat2025
   :members:
   :undoc-members:

zheng2024
~~~~~~~~~
.. automodule:: amocatlas.data_sources.zheng2024
   :members:
   :undoc-members:

nac
~~~
.. automodule:: amocatlas.data_sources.nac
   :members:
   :undoc-members:

sf2021
~~~~~~
.. automodule:: amocatlas.data_sources.sf2021
   :members:
   :undoc-members:

lebras35n
~~~~~~~~~
.. automodule:: amocatlas.data_sources.lebras35n
   :members:
   :undoc-members:

axmoc22s
~~~~~~~~
.. automodule:: amocatlas.data_sources.axmoc22s
   :members:
   :undoc-members:

axmoc34s
~~~~~~~~
.. automodule:: amocatlas.data_sources.axmoc34s
   :members:
   :undoc-members:

ovide
~~~~~
.. automodule:: amocatlas.data_sources.ovide
   :members:
   :undoc-members:

scotia
~~~~~~
.. automodule:: amocatlas.data_sources.scotia
   :members:
   :undoc-members: