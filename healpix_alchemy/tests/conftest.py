import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def postgresql_engine(postgresql):
    return create_engine('postgresql://',
                         poolclass=StaticPool,
                         creator=lambda: postgresql)
