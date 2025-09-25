from pathlib import Path

import pytest
import xarray as xr

from amocatlas import logger, utilities

# Sample data
VALID_URL = "https://mooring.ucsd.edu/move/nc/"
INVALID_URL = "ftdp://invalid-url.com/data.nc"
INVALID_STRING = "not_a_valid_source"

# Replace with actual path to a local .nc file if you have one for local testing
LOCAL_VALID_FILE = "/path/to/your/OS_MOVE_TRANSPORTS.nc"
LOCAL_INVALID_FILE = "/path/to/invalid_file.txt"

logger.disable_logging()


@pytest.mark.parametrize(
    "url,expected",
    [
        (VALID_URL, True),
        (INVALID_URL, False),
        ("not_a_url", False),
    ],
)
def test_is_valid_url(url, expected):
    assert utilities._is_valid_url(url) == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (
            LOCAL_VALID_FILE,
            Path(LOCAL_VALID_FILE).is_file() and LOCAL_VALID_FILE.endswith(".nc"),
        ),
        (LOCAL_INVALID_FILE, False),
        ("non_existent_file.nc", False),
    ],
)
def test_is_valid_file(path, expected):
    assert utilities._is_valid_file(path) == expected


def test_safe_update_attrs_add_new_attribute():
    ds = xr.Dataset()
    new_attrs = {"project": "MOVE"}
    ds = utilities.safe_update_attrs(ds, new_attrs)
    assert ds.attrs["project"] == "MOVE"


def test_safe_update_attrs_existing_key_logs(caplog):
    from amocatlas import logger, utilities

    # Re-enable logging for this test
    logger.enable_logging()

    ds = xr.Dataset(attrs={"project": "MOVE"})
    new_attrs = {"project": "OSNAP"}

    with caplog.at_level("DEBUG", logger="amocatlas"):
        utilities.safe_update_attrs(ds, new_attrs, overwrite=False, verbose=True)

    assert any(
        "Attribute 'project' already exists in dataset attrs and will not be overwritten."
        in message
        for message in caplog.messages
    )


def test_safe_update_attrs_existing_key_with_overwrite():
    ds = xr.Dataset(attrs={"project": "MOVE"})
    new_attrs = {"project": "OSNAP"}
    ds = utilities.safe_update_attrs(ds, new_attrs, overwrite=True)
    assert ds.attrs["project"] == "OSNAP"
