import numpy as np
import sqlalchemy as sa
import pytest
from pytest_postgresql.janitor import DatabaseJanitor

from . import data, models


@pytest.fixture
def engine(postgresql_proc):
    """Create an SQLAlchemy engine with a disposable PostgreSQL database."""
    host = postgresql_proc.host
    port = postgresql_proc.port
    user = postgresql_proc.user
    password = postgresql_proc.password
    db = postgresql_proc.dbname
    version = postgresql_proc.version

    url = sa.engine.URL.create('postgresql', user, password, host, port, db)
    with DatabaseJanitor(user, host, port, db, version, password):
        yield sa.create_engine(url)


@pytest.fixture
def session(engine):
    with sa.orm.Session(engine) as session:
        yield session


@pytest.fixture
def cursor(session):
    return session.connection().connection.cursor()


@pytest.fixture
def tables(engine):
    models.Base.metadata.create_all(engine)


@pytest.fixture
def random_galaxies(cursor, tables):
    return data.get_random_galaxies(40_000, cursor)


@pytest.fixture(params=np.geomspace(1, 10_000, 10, dtype=int).tolist())
def random_fields(cursor, tables, request):
    return data.get_random_fields(request.param, cursor)


@pytest.fixture
def random_sky_map(cursor, tables):
    return data.get_random_sky_map(20_000, cursor)
