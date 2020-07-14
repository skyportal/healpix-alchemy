import itertools

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.misc import NumpyRNGContext
import numpy as np
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import aliased, sessionmaker
import pytest

from ..unit_spherical import (HasUnitSphericalCoordinate,
                              UnitSphericalCoordinate)


Base = declarative_base()


class Point1(HasUnitSphericalCoordinate, Base):
    __tablename__ = 'points1'
    id = Column(Integer, primary_key=True)


class Point2(HasUnitSphericalCoordinate, Base):
    __tablename__ = 'points2'
    id = Column(Integer, primary_key=True)


def match_sky(coords1, coords2, separation):
    """Get all matches between SkyCoord objects, not just nearest neighbors.

    The :meth:`astropy.coordinates.SkyCoord.match_to_catalog_sky` method only
    returns the `n`th neighbor for one value of `n` at a time. This method
    returns all matches.
    """
    nresults = 0
    results = np.empty((0, 2), dtype=np.intp)
    id1 = np.arange(len(coords1))

    for n in itertools.count(1):
        id2, sep, _ = coords1.match_to_catalog_sky(coords2, nthneighbor=n)
        new_results = np.column_stack((id1, id2))[sep <= separation]
        results = np.row_stack((results, new_results))
        if len(results) > 0:
            results = np.unique(results, axis=0)
        new_nresults = len(results)
        if new_nresults == nresults:
            return results
        nresults = new_nresults


@pytest.fixture
def session(postgresql_engine):
    Base.metadata.create_all(postgresql_engine)
    Session = sessionmaker(bind=postgresql_engine)
    return Session()


@pytest.fixture(params=[10, 100, 1000, 10000])
def point_clouds(request, session):
    # Generate two random point clouds
    n = request.param

    with NumpyRNGContext(8675309):
        lons = np.random.uniform(0, 360, (2, n))
        lats = np.rad2deg(np.arcsin(np.random.uniform(-1, 1, (2, n))))

    # Commit to database
    for model_cls, lons_, lats_ in zip([Point1, Point2], lons, lats):
        for i, (lon, lat) in enumerate(zip(lons_, lats_)):
            row = model_cls(id=i, coordinate=UnitSphericalCoordinate(lon, lat))
            session.add(row)
    session.commit()

    return lons, lats


def test_cross_join(benchmark, session, point_clouds):
    separation = 1  # degrees
    lons, lats = point_clouds

    # Find all matches within :var:`separation` degrees
    def do_query():
        return session.query(
            Point1.id, Point2.id
        ).join(
            Point2,
            Point1.coordinate.within(Point2.coordinate, separation)
        ).order_by(
            Point1.id, Point2.id
        ).all()
    result = benchmark(do_query)
    matches = np.asarray(result).reshape(-1, 2)

    # Find all matches using Astropy
    coords1, coords2 = (SkyCoord(lons_, lats_, unit=(u.deg, u.deg))
                        for lons_, lats_ in zip(lons, lats))
    expected_matches = match_sky(coords1, coords2, separation * u.deg)

    # Compare SQLAlchemy result to Astropy
    np.testing.assert_array_equal(matches, expected_matches)


def test_self_join(benchmark, session, point_clouds):
    def do_query():
        table1 = aliased(Point1)
        table2 = aliased(Point2)
        return session.query(
            table1.id, table2.id
        ).join(
            table2,
            table1.coordinate.within(table2.coordinate, 1)
        ).order_by(
            table1.id, table2.id
        ).all()
    benchmark(do_query)


def test_cone_search(benchmark, session, point_clouds):
    def do_query():
        table1 = aliased(Point1)
        table2 = aliased(Point2)
        return session.query(
            table1.id, table2.id
        ).join(
            table2,
            table1.coordinate.within(table2.coordinate, 1)
        ).filter(
            table1.id == 0
        ).order_by(
            table2.id
        ).all()
    benchmark(do_query)
