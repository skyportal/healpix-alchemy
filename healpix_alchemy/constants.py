import sqlalchemy as sa
from astropy import units as u
from astropy.coordinates import ICRS
from astropy_healpix import HEALPix, level_to_nside
from mocpy import MOC

LEVEL = int(MOC.MAX_ORDER)
"""Base HEALPix resolution. This is the maximum HEALPix level that can be
stored in a signed 8-byte integer data type.

Coerced to a Python :class:`int` because newer versions of mocpy return
:class:`numpy.uint8`, which would silently overflow in expressions like
``4**LEVEL``."""

HPX = HEALPix(nside=level_to_nside(LEVEL), order="nested", frame=ICRS())
"""HEALPix projection object."""

PIXEL_AREA = HPX.pixel_area.to_value(u.sr)
"""Native pixel area in steradians."""

PIXEL_AREA_LITERAL = sa.literal(PIXEL_AREA, sa.Float)
"""Pixel area as an SQL literal."""
