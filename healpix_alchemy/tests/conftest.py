import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def engine(postgresql):
    """Create an SQLAlchemy engine with a disposable PostgreSQL database."""
    return create_engine('postgresql://',
                         poolclass=StaticPool,
                         creator=lambda: postgresql)


@pytest.fixture
def session(engine):
    """Create an SQLAlchemy session with a disposable PostgreSQL database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
