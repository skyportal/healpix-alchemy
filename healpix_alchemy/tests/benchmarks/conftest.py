import numpy as np
import sqlalchemy as sa
from sqlalchemy import orm
import pytest

from . import data, models


@pytest.fixture
def engine(postgresql):
    return sa.create_engine('postgresql://', poolclass=sa.pool.StaticPool,
                            creator=lambda: postgresql)


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


@pytest.fixture(params=[2000])
def random_fields(cursor, tables, request):
    return data.get_random_fields(request.param, cursor)


@pytest.fixture()
def ztf_fields(cursor, tables):
    return data.get_ztf_fields(cursor)


@pytest.fixture(params=np.geomspace(1, 1000, 10, dtype=int).tolist())
# @pytest.fixture(params=[50])
def random_sky_map(cursor, tables, request):
    return data.get_random_sky_map(20_000, request.param, cursor)
