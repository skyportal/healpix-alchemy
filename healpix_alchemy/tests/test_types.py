import numpy as np
from mocpy import MOC
import itertools
from astropy_healpix import HEALPix

from .. import types


def random_MOC(max_l):
    json = {str(level): list(
        np.unique(
            np.random.randint(0, 12 * (4 ** level),
                              np.random.randint(12 * (4 ** level)))))
            for level in range(max_l)}
    return MOC.from_json(json), json


def to_ranges(iterable):
    iterable = sorted(set(iterable))
    for key, group in itertools.groupby(enumerate(iterable),
                                        lambda t: t[1] - t[0]):
        group = list(group)
        yield group[0][1], group[-1][1]+1


def test_to_moc_ring():
    l_lim = 12
    moc, json = random_MOC(l_lim)
    for level in range(l_lim-1):
        for pixel in json[str(level)]:
            for i in range(4):
                json[str(level + 1)].append(pixel * 4 + i)
        json[str(level + 1)] = np.unique(json[str(level + 1)])
    nested_hpx_list = json[str(l_lim-1)]
    hp = HEALPix(nside=2**(l_lim-1), order='ring')
    ring_hpx_list = hp.nested_to_ring(nested_hpx_list)
    ring_hpx_ranges = to_ranges(ring_hpx_list)
    point = types.Point()
    assert point.to_moc(rangeSet=ring_hpx_ranges,
                        nside=2**(l_lim-1),
                        index='ring') == moc


def test_to_moc_nested():
    l_lim = 12
    moc, json = random_MOC(l_lim)
    for level in range(l_lim-1):
        for pixel in json[str(level)]:
            for i in range(4):
                json[str(level + 1)].append(pixel * 4 + i)
        json[str(level + 1)] = np.unique(json[str(level + 1)])
    nested_hpx_list = json[str(l_lim-1)]
    nested_hpx_ranges = to_ranges(nested_hpx_list)
    point = types.Point()
    assert point.to_moc(rangeSet=nested_hpx_ranges,
                        nside=2**(l_lim-1),
                        index='nested') == moc
