import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def postgresql_engine(postgresql):
    """Create an SQLAlchemy engine with a disposable PostgreSQL database."""
    return create_engine('postgresql://',
                         poolclass=StaticPool,
                         creator=lambda: postgresql)
