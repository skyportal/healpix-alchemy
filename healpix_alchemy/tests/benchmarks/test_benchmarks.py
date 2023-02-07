from functools import reduce
from .explain import explain

import numpy as np
import sqlalchemy as sa
import pytest

from ... import temporary_table, func
from .models import Galaxy, FieldTile, SkymapTile


@pytest.fixture
def bench(benchmark, session):

    def _func(query):
        session.execute(sa.text('ANALYZE'))
        return benchmark(lambda: session.execute(query).all())

    return _func


@pytest.fixture
def bench_and_check(bench):

    def _func(query, expected):
        np.testing.assert_almost_equal(bench(query), expected, decimal=6)

    return _func


# def test_union_area(bench_and_check, random_fields):
#     """Find the area of the union of N fields."""
#     # Assemble query
#     subquery = sa.select(
#         func.union(FieldTile.hpx).label('hpx')
#     ).subquery()
#     query = sa.select(
#         sa.func.sum(subquery.columns.hpx.area)
#     )

#     # Expected result
#     union = reduce(lambda a, b: a.union(b), random_fields)
#     result = union.sky_fraction * 4 * np.pi
#     expected = ((result,),)

#     # Run benchmark, check result
#     bench_and_check(query, expected)


# def test_crossmatch_galaxies_and_fields(bench_and_check,
#                                         random_fields, random_galaxies):
#     """Cross match N galaxies with M fields."""
#     # Assemble query
#     count = sa.func.count(Galaxy.id)
#     query = sa.select(
#         count
#     ).filter(
#         FieldTile.hpx.contains(Galaxy.hpx)
#     ).group_by(
#         FieldTile.id
#     ).order_by(
#         count.desc()
#     ).limit(
#         5
#     )

#     # Expected result
#     points = random_galaxies
#     fields = random_fields
#     result = np.sum(
#         [moc.contains(points.ra, points.dec) for moc in fields],
#         axis=1)
#     expected = np.flipud(np.sort(result))[:5].reshape(-1, 1)

#     # Run benchmark, check result
#     bench_and_check(query, expected)


# def test_fields_in_90pct_credible_region(bench, random_fields, random_sky_map):
#     """Find which of N fields overlap the 90% credible region."""
#     # Assemble query
#     cum_prob = sa.func.sum(
#         SkymapTile.probdensity * SkymapTile.hpx.area
#     ).over(
#         order_by=SkymapTile.probdensity.desc()
#     ).label(
#         'cum_prob'
#     )
#     subquery1 = sa.select(
#         SkymapTile.probdensity,
#         cum_prob
#     ).filter(
#         SkymapTile.id == 1
#     ).subquery()
#     min_probdensity = sa.select(
#         sa.func.min(subquery1.columns.probdensity)
#     ).filter(
#         subquery1.columns.cum_prob <= 0.9
#     ).scalar_subquery()
#     query = sa.select(
#         sa.func.count(FieldTile.id.distinct())
#     ).filter(
#         SkymapTile.hpx.overlaps(FieldTile.hpx),
#         SkymapTile.probdensity >= min_probdensity
#     )

#     # Run benchmark
#     bench(query)


def test_integrated_probability(bench, ztf_fields, random_sky_map, session):
    """Find integrated probability within union of fields."""
    union = sa.select(
        func.union(FieldTile.hpx).label('hpx')
    ).filter(
        FieldTile.id.between(100, 120)
    ).subquery()

    area = (union.columns.hpx * SkymapTile.hpx).area
    prob = sa.func.sum(SkymapTile.probdensity * area)

    query = sa.select(
        prob
    ).filter(
        SkymapTile.id == 1,
        union.columns.hpx.overlaps(SkymapTile.hpx)
    )

    session.execute('ANALYZE')
    session.execute("LOAD 'auto_explain'")
    session.execute("SET auto_explain.log_min_duration=0")
    session.execute("SET auto_explain.log_analyze=true")
    session.execute(query).all()
    session.execute("SET auto_explain.log_min_duration='1000s'")
