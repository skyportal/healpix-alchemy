import itertools

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.misc import NumpyRNGContext
import numpy as np
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import aliased
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


@pytest.fixture(params=[10, 100, 1000, 10000])
def point_clouds(request, session, engine):
    """Generate two random point clouds."""
    Base.metadata.create_all(engine)

    n = request.param

    with NumpyRNGContext(8675309):
        ras = np.random.uniform(0, 360, (2, n))
        decs = np.rad2deg(np.arcsin(np.random.uniform(-1, 1, (2, n))))

    # Commit to database
    for model_cls, ras_, decs_ in zip([Point1, Point2], ras, decs):
        for i, (ra, dec) in enumerate(zip(ras_, decs_)):
            row = model_cls(id=i, coordinate=UnitSphericalCoordinate(ra, dec))
            session.add(row)
    session.commit()

    return ras, decs


SEPARATION = 1  # Separation in degrees for unit tests below


def test_cross_join(benchmark, session, point_clouds):
    ras, decs = point_clouds

    def do_query():
        return session.query(
            Point1.id, Point2.id
        ).join(
            Point2,
            Point1.coordinate.within(Point2.coordinate, SEPARATION)
        ).order_by(
            Point1.id, Point2.id
        ).all()

    result = benchmark(do_query)
    matches = np.asarray(result).reshape(-1, 2)

    # Find all matches using Astropy
    coords1, coords2 = (SkyCoord(ras_, decs_, unit=(u.deg, u.deg))
                        for ras_, decs_ in zip(ras, decs))
    expected_matches = match_sky(coords1, coords2, SEPARATION * u.deg)

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
            table1.coordinate.within(table2.coordinate, SEPARATION)
        ).order_by(
            table1.id, table2.id
        ).all()

    benchmark(do_query)


def test_cone_search(benchmark, session, point_clouds):
    target = session.query(Point1).get(0)

    def do_query():
        return session.query(
            Point1.id
        ).filter(
            Point1.coordinate.within(target.coordinate, SEPARATION)
        ).order_by(
            Point1.id
        ).all()

    benchmark(do_query)


def test_cone_search_literal(benchmark, session, point_clouds):
    target = UnitSphericalCoordinate(100.0, 20.0)

    def do_query():
        return session.query(
            Point1.id
        ).filter(
            Point1.coordinate.within(target, SEPARATION)
        ).order_by(
            Point1.id
        ).all()

    benchmark(do_query)
