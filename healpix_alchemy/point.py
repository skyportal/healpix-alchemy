"""Spatial indexing for astronomical point coordinates."""
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.schema import Column, Index
from sqlalchemy.sql import and_
from sqlalchemy.types import Float

from .math import sind, cosd

__all__ = ('Point',)


class Point:
    """Mixin class to add a point to a an SQLAlchemy declarative model."""

    def __init__(self, *args, ra=None, dec=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ra = ra
        self.dec = dec

    ra = Column(Float)
    dec = Column(Float)

    @hybrid_property
    def cartesian(self):
        """Convert to Cartesian coordinates.

        Returns
        -------
        x, y, z : float
            A tuple of the x, y, and z coordinates.

        """
        return (cosd(self.ra) * cosd(self.dec),
                sind(self.ra) * cosd(self.dec),
                sind(self.dec))

    @hybrid_method
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

    @declared_attr
    def __table_args__(cls):
        try:
            args = super().__table_args__
        except AttributeError:
            args = ()
        args += (Index(f'ix_{cls.__tablename__}_point', *cls.cartesian),)
        return args
