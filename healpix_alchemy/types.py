"""SQLAlchemy types for multiresolution HEALPix data."""

from collections.abc import Iterator, Sequence

import numpy as np
import sqlalchemy as sa
from astropy.coordinates import SkyCoord
from astropy_healpix import uniq_to_level_ipix
from mocpy import MOC
from numpy.typing import ArrayLike
from sqlalchemy.dialects.postgresql import INT8RANGE

from .constants import HPX, LEVEL, PIXEL_AREA_LITERAL

__all__ = ("Point", "Tile")


class Point(sa.TypeDecorator[int]):
    cache_ok = True
    impl = sa.BigInteger

    def process_bind_param(
        self,
        value: SkyCoord | tuple[float, float] | np.integer | int | None,
        dialect: sa.Dialect,
    ) -> int | None:
        if isinstance(value, SkyCoord):
            value = HPX.skycoord_to_healpix(value)
        elif isinstance(value, Sequence) and len(value) == 2:
            value = HPX.lonlat_to_healpix(*value)
        if isinstance(value, np.integer):
            value = int(value)
        return value


class Tile(sa.TypeDecorator[str]):
    cache_ok = True
    impl = INT8RANGE

    def process_bind_param(
        self,
        value: int | np.integer | tuple[int, int] | str | None,
        dialect: sa.Dialect,
    ) -> str | None:
        if isinstance(value, (int, np.integer)):
            level, ipix = uniq_to_level_ipix(value)
            shift = 2 * (LEVEL - level)
            value = (ipix << shift, (ipix + 1) << shift)
        if isinstance(value, Sequence) and len(value) == 2:
            value = f"[{value[0]},{value[1]})"
        return value

    class comparator_factory(INT8RANGE.comparator_factory):
        @property
        def lower(self) -> sa.ColumnElement[int]:
            return sa.func.lower(self, type_=Point)

        @property
        def upper(self) -> sa.ColumnElement[int]:
            return sa.func.upper(self, type_=Point)

        @property
        def length(self) -> sa.ColumnElement[int]:
            return self.upper - self.lower

        @property
        def area(self) -> sa.ColumnElement[float]:
            return sa.type_coerce(self.length * PIXEL_AREA_LITERAL, sa.Float)

    @classmethod
    def tiles_from(cls, obj: MOC | SkyCoord) -> Iterator[str]:
        if isinstance(obj, MOC):
            return cls.tiles_from_moc(obj)
        elif isinstance(obj, SkyCoord):
            return cls.tiles_from_polygon_skycoord(obj)
        else:
            raise TypeError("Unknown type")

    @classmethod
    def tiles_from_polygon_skycoord(cls, polygon: SkyCoord) -> Iterator[str]:
        return cls.tiles_from_moc(
            MOC.from_polygon_skycoord(polygon.transform_to(HPX.frame))
        )

    @classmethod
    def tiles_from_moc(cls, moc: MOC) -> Iterator[str]:
        return (f"[{lo},{hi})" for lo, hi in moc.to_depth29_ranges)

    @classmethod
    def tiles_from_uniq(cls, uniq: ArrayLike) -> Iterator[str]:
        """Convert an array of UNIQ indices to tile range strings."""
        level, ipix = uniq_to_level_ipix(np.asarray(uniq, dtype=np.int64))
        shift = 2 * (LEVEL - level)
        lo = ipix << shift
        hi = (ipix + 1) << shift
        return (f"[{a},{b})" for a, b in zip(lo.tolist(), hi.tolist()))


@sa.event.listens_for(sa.Index, "after_parent_attach")
def _create_indices(index: sa.Index, parent: sa.Table) -> None:
    """Set index method to SP-GiST_ for any indexed Tile or Region columns.

    .. _SP-GiST: https://www.postgresql.org/docs/current/spgist.html
    """
    if (
        index._column_flag
        and len(index.expressions) == 1
        and isinstance(index.expressions[0], sa.Column)
        and isinstance(index.expressions[0].type, Tile)
    ):
        index.dialect_options["postgresql"]["using"] = "spgist"
