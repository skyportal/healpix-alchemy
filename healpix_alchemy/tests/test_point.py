import itertools

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.misc import NumpyRNGContext
import numpy as np
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import aliased
import pytest

from .. import Point


Base = declarative_base()


class Catalog1(Point, Base):
    __tablename__ = 'catalog1'
    id = Column(Integer, primary_key=True)


class Catalog2(Point, Base):
    __tablename__ = 'catalog2'
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
    for model_cls, ras_, decs_ in zip([Catalog1, Catalog2], ras, decs):
        for i, (ra, dec) in enumerate(zip(ras_, decs_)):
            row = model_cls(id=i, ra=ra, dec=dec)
            session.add(row)
    session.commit()

    return ras, decs


SEPARATION = 1  # Separation in degrees for unit tests below


def test_cross_join(benchmark, session, point_clouds):
    ras, decs = point_clouds

    def do_query():
        return session.query(
            Catalog1.id, Catalog2.id
        ).join(
            Catalog2,
            Catalog1.within(Catalog2, SEPARATION)
        ).order_by(
            Catalog1.id, Catalog2.id
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
        table1 = aliased(Catalog1)
        table2 = aliased(Catalog1)
        return session.query(
            table1.id, table2.id
        ).join(
            table2,
            table1.within(table2, SEPARATION)
        ).order_by(
            table1.id, table2.id
        ).all()

    benchmark(do_query)


def test_cone_search(benchmark, session, point_clouds):
    target = session.query(Catalog1).get(0)

    def do_query():
        return session.query(
            Catalog1.id
        ).filter(
            Catalog1.within(target, SEPARATION)
        ).order_by(
            Catalog1.id
        ).all()

    benchmark(do_query)


def test_cone_search_literal_lhs(benchmark, session, point_clouds):
    target = Point(ra=100.0, dec=20.0)

    def do_query():
        return session.query(
            Catalog1.id
        ).filter(
            Catalog1.within(target, SEPARATION)
        ).order_by(
            Catalog1.id
        ).all()

    benchmark(do_query)


def test_cone_search_literal_rhs(benchmark, session, point_clouds):
    target = Point(ra=100.0, dec=20.0)

    def do_query():
        return session.query(
            Catalog1.id
        ).filter(
            target.within(Catalog1, SEPARATION)
        ).order_by(
            Catalog1.id
        ).all()

    benchmark(do_query)
