"""Spatial indexing for astronomical point coordinates."""
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.schema import Column, Index
from sqlalchemy.sql import and_
from sqlalchemy.types import Float

from .math import sind, cosd

__all__ = ('Point', 'HasPoint', 'HasNullablePoint')


class Point(Comparator):

    def __init__(self, ra, dec):
        self._ra = ra
        self._dec = dec

    @property
    def cartesian(self):
        """Convert to Cartesian coordinates.

        Returns
        -------
        x, y, z : float
            A tuple of the x, y, and z coordinates.

        """
        return (cosd(self._ra) * cosd(self._dec),
                sind(self._ra) * cosd(self._dec),
                sind(self._dec))

    def within(self, other, radius):
        """Test if this point is within a given radius of another point.

        Parameters
        ----------
        other : Point
            The other point.
        radius : float
            The match radius in degrees.

        Returns
        -------
        bool

        """
        sin_radius = sind(radius)
        cos_radius = cosd(radius)
        carts = (obj.cartesian for obj in (self, other))
        terms = ((lhs.between(rhs - 2 * sin_radius, rhs + 2 * sin_radius),
                  lhs * rhs) for lhs, rhs in zip(*carts))
        bounding_box_terms, dot_product_terms = zip(*terms)
        return and_(*bounding_box_terms, sum(dot_product_terms) >= cos_radius)


def point_factory(nullable=False):
    
    class _HasPoint:
        """Mixin class to add a point to a an SQLAlchemy declarative model."""

        ra = Column(Float, nullable=nullable)
        dec = Column(Float, nullable=nullable)

        @hybrid_property
        def point(self):
            return Point(self.ra, self.dec)

        @point.setter
        def point(self, value):
            self.ra = value._ra
            self.dec = value._dec

        @declared_attr
        def __table_args__(cls):
            try:
                args = super().__table_args__
            except AttributeError:
                args = ()
            args += tuple(Index(f'{cls.__tablename__}_{k}_index', v)
                          for k, v in zip('xyz', cls.point.cartesian))
            return args

    return _HasPoint

HasPoint = point_factory()
HasNullablePoint = point_factory(nullable=True)
