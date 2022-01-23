"""Pytest configuration for running the doctests in README.md."""
from unittest.mock import Mock
import sqlalchemy as sa
import pytest

from healpix_alchemy.tests.benchmarks.conftest import engine  # noqa: F401


@pytest.fixture(autouse=True)
def add_mock_create_engine(monkeypatch, request):
    """Monkey patch sqlalchemy.create_engine for doctests in README.md."""
    if request.node.name == 'README.md':
        db_engine = request.getfixturevalue('engine')
        monkeypatch.setattr(sa, 'create_engine', Mock(return_value=db_engine))
