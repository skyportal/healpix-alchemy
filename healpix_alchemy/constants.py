from astropy.coordinates import ICRS
from astropy import units as u
from astropy_healpix import level_to_nside, HEALPix
from mocpy import IntervalSet
import sqlalchemy as sa

LEVEL = IntervalSet.HPX_MAX_ORDER
"""Base HEALPix resolution. This is the maximum HEALPix level that can be
stored in a signed 8-byte integer data type."""

HPX = HEALPix(nside=level_to_nside(LEVEL), order='nested', frame=ICRS())
"""HEALPix projection object."""

PIXEL_AREA = HPX.pixel_area.to_value(u.sr)
"""Native pixel area in steradians."""

PIXEL_AREA_LITERAL = sa.literal(PIXEL_AREA, sa.Float)
"""Pixel area as an SQL literal."""
