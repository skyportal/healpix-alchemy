import numpy as np
import pytest
from sqlalchemy import orm

from . import data, models


@pytest.fixture
def session(engine):
    with orm.Session(engine) as session:
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
