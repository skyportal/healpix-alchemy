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


def class_factory(lon_name='lon', lat_name='lat', nullable=False):

    class _SphericalCoordinateBase(object):

        @hybrid_method
        def within(self, other, radius):
            sin_radius = sind(radius)
            cos_radius = cosd(radius)
            carts = list(zip(*(obj.cartesian() for obj in (self, other))))
            return and_(
                *(lhs.between(rhs - 2 * sin_radius, rhs + 2 * sin_radius)
                  for lhs, rhs in carts),
                sum(lhs * rhs for lhs, rhs in carts) >= cos_radius)

        @hybrid_method
        def cartesian(self):
            lon = getattr(self, self.lon_name)
            lat = getattr(self, self.lat_name)
            return _to_cartesian(lon, lat)

        @declared_attr
        def __table_args__(cls):

            lon = getattr(cls, cls.lon_name)
            lat = getattr(cls, cls.lat_name)

            try:
                args = super().__table_args__
            except AttributeError:
                args = ()
            args += tuple(Index(f'{cls.__tablename__}_{k}_index', v)
                          for k, v in zip('xyz', _to_cartesian(lon, lat)))
            return args

    lon = Column(lon_name, Float, nullable=nullable)
    lat = Column(lat_name, Float, nullable=nullable)

    setattr(_SphericalCoordinateBase, lon_name, lon)
    setattr(_SphericalCoordinateBase, lat_name, lat)

    _SphericalCoordinateBase.lon_name = lon_name
    _SphericalCoordinateBase.lat_name = lat_name

    return _SphericalCoordinateBase


HasUnitSphericalCoordinate = class_factory()
HasRADec = class_factory('ra', 'dec')
