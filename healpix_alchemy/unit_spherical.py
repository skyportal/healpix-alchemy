from dataclasses import astuple, dataclass

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Column, Index
from sqlalchemy.sql import and_
from sqlalchemy.types import Float
from sqlalchemy.ext.hybrid import hybrid_method

from .math import sind, cosd

__all__ = ('HasUnitSphericalCoordinate',)


def _to_cartesian(lon, lat):
    return cosd(lon) * cosd(lat), sind(lon) * cosd(lat), sind(lat)


class HasUnitSphericalCoordinate:

    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)

    @hybrid_method
    def cartesian(self):
        return _to_cartesian(self.lon, self.lat)

    @hybrid_method
    def within(self, other, radius):
        sin_radius = sind(radius)
        cos_radius = cosd(radius)
        carts = list(zip(*(obj.cartesian() for obj in (self, other))))
        return and_(*(lhs.between(rhs - 2 * sin_radius, rhs + 2 * sin_radius)
                      for lhs, rhs in carts),
                    sum(lhs * rhs for lhs, rhs in carts) >= cos_radius)

    @declared_attr
    def __table_args__(cls):
        try:
            args = super().__table_args__
        except AttributeError:
            args = ()
        args += tuple(Index(f'{cls.__tablename__}_{k}_index', v)
                      for k, v in zip('xyz', _to_cartesian(cls.lon, cls.lat)))
        return args
