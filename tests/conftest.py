"""Pytest configuration for EasyPdfForYou tests."""

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory."""
    import pathlib
    return pathlib.Path(__file__).parent / "data"