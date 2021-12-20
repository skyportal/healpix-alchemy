import numpy as np
from mocpy import MOC
import itertools
from astropy_healpix import HEALPix
from astropy.coordinates import Angle, Longitude, Latitude
import astropy.units as u

from .. import types


def to_ranges(iterable):
    iterable = sorted(set(iterable))
    for key, group in itertools.groupby(enumerate(iterable),
                                        lambda t: t[1] - t[0]):
        group = list(group)
        yield group[0][1], group[-1][1]+1


def test_to_moc():
    depth = 5
    rng = np.random.default_rng()
    lon = Longitude(360 * rng.random() * u.deg)
    lat = Latitude((180 * rng.random() - 90) * u.deg)
    radius = Angle(rng.normal(loc=10, scale=2.5) * u.deg)
    moc = MOC.from_cone(lon, lat, radius, depth)
    hp = HEALPix(nside=2**depth, order='nested')
    healpix_list = hp.cone_search_lonlat(lon, lat, radius)
    nested_hpx_ranges = [item for item in to_ranges(healpix_list)]

    assert types.Point.to_moc(rangeSet=nested_hpx_ranges,
                        nside=2**depth) == moc
