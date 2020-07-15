import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(params=['mysql', 'postgresql'])
def engine(request):
    """Parametrize SQLAlchemy engines over SQLite and PostgreSQL."""
    connection = request.getfixturevalue(request.param)
    return create_engine(URL(request.param),
                         poolclass=StaticPool,
                         creator=lambda: connection)


@pytest.fixture
def session(engine):
    """Create an SQLAlchemy session with a disposable database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
