"""Spatial indexing for astronomical point coordinates."""
from math import cos, radians as rad, sin

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.schema import Column, Index
from sqlalchemy.sql import and_, between
from sqlalchemy.types import Float
from sqlalchemy import BigInteger

import astropy.units as u

from .util import default_and_onupdate as dfl, InheritTableArgs
from .healpix import LEVEL, HPX

__all__ = ('Point',)


class Point(InheritTableArgs):
    """Mixin class to add a point to a an SQLAlchemy declarative model."""

    def __init__(self, *args, ra=None, dec=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ra = ra
        self.dec = dec

    ra = Column(Float)
    dec = Column(Float)

    x = Column(
        'x', Float, doc='Cached and precomputed Cartesian "x" coordinate',
        **dfl(lambda ra, dec: cos(rad(ra)) * cos(rad(dec))))

    y = Column(
        'y', Float, doc='Cached and precomputed Cartesian "y" coordinate',
        **dfl(lambda ra, dec: sin(rad(ra)) * cos(rad(dec))))

    z = Column(
        'z', Float, doc='Cached and precomputed Cartesian "z" coordinate',
        **dfl(lambda dec: sin(rad(dec))))

    nested = Column(
        BigInteger, index=True,
        doc=f'Cached and precomputed HEALPix nested index at nside=2**{LEVEL}',
        **dfl(lambda ra, dec: int(HPX.lonlat_to_healpix(ra*u.deg, dec*u.deg))))

    @hybrid_property
    def cartesian(self):
        """Convert to Cartesian coordinates.

        Returns
        -------
        x, y, z : float
            A tuple of the x, y, and z coordinates.

        """
        return (self.x, self.y, self.z)

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
        sin_radius = sin(rad(radius))
        cos_radius = cos(rad(radius))
        carts = (obj.cartesian for obj in (self, other))
        # Evaluate boolean expressions for bounding box test
        # and dot product
        terms = ((between(lhs, rhs - 2 * sin_radius, rhs + 2 * sin_radius),
                  lhs * rhs) for lhs, rhs in zip(*carts))
        bounding_box_terms, dot_product_terms = zip(*terms)
        return and_(*bounding_box_terms, sum(dot_product_terms) >= cos_radius)

    @declared_attr
    def __table_args__(cls):
        *args, kwargs = super().__table_args__
        index = Index(f'ix_{cls.__tablename__}_point', *cls.cartesian)
        return (*args, index, kwargs)
