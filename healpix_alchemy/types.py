"""SQLAlchemy types for multiresolution HEALPix data."""
from collections.abc import Sequence
from numbers import Integral

from astropy.coordinates import SkyCoord
from astropy_healpix import uniq_to_level_ipix
from mocpy import MOC
import numpy as np
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INT8RANGE

from .constants import HPX, LEVEL, PIXEL_AREA_LITERAL

__all__ = ('Point', 'Tile')


class Point(sa.TypeDecorator):

    cache_ok = True
    impl = sa.BigInteger

    def process_bind_param(self, value, dialect):
        if isinstance(value, SkyCoord):
            value = HPX.skycoord_to_healpix(value)
        elif isinstance(value, Sequence) and len(value) == 2:
            value = HPX.lonlat_to_healpix(*value)
        if isinstance(value, np.int64):
            value = int(value)
        return value


class Tile(sa.TypeDecorator):

    cache_ok = True
    impl = INT8RANGE

    def process_bind_param(self, value, dialect):
        if isinstance(value, Integral):
            level, ipix = uniq_to_level_ipix(value)
            shift = 2 * (LEVEL - level)
            value = (ipix << shift, (ipix + 1) << shift)
        if isinstance(value, Sequence) and len(value) == 2:
            value = f'[{value[0]},{value[1]})'
        return value

    class comparator_factory(INT8RANGE.comparator_factory):

        @property
        def lower(self):
            return sa.func.lower(self, type_=Point)

        @property
        def upper(self):
            return sa.func.upper(self, type_=Point)

        @property
        def length(self):
            return self.upper - self.lower

        @property
        def area(self):
            return self.length * PIXEL_AREA_LITERAL

    @classmethod
    def tiles_from(cls, obj):
        if isinstance(obj, MOC):
            return cls.tiles_from_moc(obj)
        elif isinstance(obj, SkyCoord):
            return cls.tiles_from_polygon_skycoord(obj)
        else:
            raise TypeError('Unknown type')

    @classmethod
    def tiles_from_polygon_skycoord(cls, polygon):
        return cls.tiles_from_moc(
            MOC.from_polygon_skycoord(
                polygon.transform_to(HPX.frame)))

    @classmethod
    def tiles_from_moc(cls, moc):
        return (f'[{lo},{hi})' for lo, hi in moc._interval_set.nested)


@sa.event.listens_for(sa.Index, 'after_parent_attach')
def _create_indices(index, parent):
    """Set index method to SP-GiST_ for any indexed Tile or Region columns.

    .. _SP-GiST: https://www.postgresql.org/docs/current/spgist.html
    """
    if (
        index._column_flag and
        len(index.expressions) == 1 and
        isinstance(index.expressions[0], sa.Column) and
        isinstance(index.expressions[0].type, Tile)
    ):
        index.dialect_options['postgresql']['using'] = 'spgist'
