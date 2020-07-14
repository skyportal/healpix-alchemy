from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.schema import Column, Index
from sqlalchemy.sql import and_
from sqlalchemy.types import Float

from .math import sind, cosd

__all__ = ('UnitSphericalCoordinate', 'HasUnitSphericalCoordinate')


class UnitSphericalCoordinate(Comparator):

    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    @property
    def cartesian(self):
        return (cosd(self.lon) * cosd(self.lat),
                sind(self.lon) * cosd(self.lat),
                sind(self.lat))

    def within(self, other, radius):
        sin_radius = sind(radius)
        cos_radius = cosd(radius)
        carts = (obj.cartesian for obj in (self, other))
        terms = ((lhs.between(rhs - 2 * sin_radius, rhs + 2 * sin_radius),
                  lhs * rhs) for lhs, rhs in zip(*carts))
        bounding_box_terms, dot_product_terms = zip(*terms)
        return and_(*bounding_box_terms, sum(dot_product_terms) >= cos_radius)


class HasUnitSphericalCoordinate:

    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)

    @hybrid_property
    def coordinate(self):
        return UnitSphericalCoordinate(self.lon, self.lat)

    @coordinate.setter
    def coordinate(self, value):
        self.lon = value.lon
        self.lat = value.lat

    @declared_attr
    def __table_args__(cls):
        try:
            args = super().__table_args__
        except AttributeError:
            args = ()
        args += tuple(Index(f'{cls.__tablename__}_{k}_index', v)
                      for k, v in zip('xyz', cls.coordinate.cartesian))
        return args
