"""Pytest fixture for monkey patching the download_file function.

This replaces the real download logic with a fake function during tests,
so that no actual network requests are made. Instead, the fake function
creates a dummy local file. Keeps tests fast, isolated, and reliable.
"""

from pathlib import Path

import pytest


@pytest.fixture()
def mock_download_file(monkeypatch):
    """Fixture to mock the download_file function in utilities.py.
    Instead of downloading, it writes dummy data to the destination.
    """

    def fake_download_file(source_url, dest_folder):
        destination = Path(dest_folder) / Path(source_url).name
        assert destination.parent.exists(), "Destination folder does not exist in mock."
        destination.write_text("fake data")
        return str(destination)

    monkeypatch.setattr("amocatlas.utilities.download_file", fake_download_file)
