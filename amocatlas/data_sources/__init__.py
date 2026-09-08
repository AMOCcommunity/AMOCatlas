"""AMOCatlas data source readers.

This package contains individual reader modules for each AMOC data source,
including observing arrays, datasets, and overflow measurements.

Each module provides a read function for accessing its specific data source
with consistent interfaces and error handling.

Module naming convention:
- Arrays include latitude: rapid26n, move16n, osnap55n, samba34s
- Special locations: wh41n (Willis & Hobbs), noac47n (North Atlantic Ocean Current)
- Datasets by author/year: fw2015, calafat2025, zheng2024
- Overflow locations: dso (Denmark Strait), fbc (Faroe Bank Channel)
"""

# Import reader functions with clean naming
from .arcticgateway import read_arcticgateway
from .axmoc22s import read_axmoc22s
from .axmoc34s import read_axmoc34s
from .calafat2025 import read_calafat2025
from .dso import read_dso
from .fbc import read_fbc
from .fw2015 import read_fw2015
from .lebras35n import read_lebras35n
from .mocha26n import read_mocha
from .move16n import read_move
from .nac import read_nac
from .noac47n import read_47n
from .osnap55n import read_osnap, read_osnap_2025
from .ovide import read_ovide
from .rapid26n import read_rapid
from .samba34s import read_samba
from .scotia import read_scotia
from .sf2021 import read_sf2021
from .wh41n import read_41n
from .zheng2024 import read_zheng2024

__all__ = [
    "read_rapid",
    "read_move",
    "read_osnap",
    "read_osnap_2025",
    "read_samba",
    "read_fw2015",
    "read_mocha",
    "read_arcticgateway",
    "read_dso",
    "read_fbc",
    "read_calafat2025",
    "read_zheng2024",
    "read_41n",
    "read_47n",
    "read_nac",
    "read_sf2021",
    "read_lebras35n",
    "read_axmoc22s",
    "read_axmoc34s",
    "read_ovide",
    "read_scotia",
]
