"""Unit tests for healpix_alchemy.types that do not require a database."""

import numpy as np
import pytest

from healpix_alchemy.constants import LEVEL
from healpix_alchemy.types import Tile


def _uniq_and_range(level, ipix):
    """Construct a UNIQ index and its expected ``[lo,hi)`` range string.

    This is the definition of the UNIQ (NUNIQ) encoding,
    ``uniq = ipix + 4 ** (level + 1)``, used as an independent ground truth.
    """
    uniq = ipix + 4 ** (level + 1)
    shift = 2 * (LEVEL - level)
    return uniq, f"[{ipix << shift},{(ipix + 1) << shift})"


@pytest.fixture
def uniq_and_expected():
    """UNIQ indices and expected ranges across every level, incl. boundaries."""
    rng = np.random.default_rng(12345)
    out = {}
    for level in range(LEVEL + 1):
        npix = 12 * 4**level
        for ipix in {0, npix - 1, *rng.integers(0, npix, size=8).tolist()}:
            uniq, expected = _uniq_and_range(level, int(ipix))
            out[uniq] = expected
    uniq = np.array(sorted(out), dtype=np.int64)
    return uniq, [out[u] for u in uniq.tolist()]


def test_tiles_from_uniq(uniq_and_expected):
    """The helper decodes UNIQ indices to the correct ranges at every level."""
    uniq, expected = uniq_and_expected
    assert list(Tile.tiles_from_uniq(uniq)) == expected


def test_tiles_from_uniq_boundary_pixel():
    """The last pixel of each level decodes correctly (worst case for log2)."""
    for level in range(LEVEL + 1):
        npix = 12 * 4**level
        uniq, expected = _uniq_and_range(level, npix - 1)
        assert list(Tile.tiles_from_uniq([uniq])) == [expected]


def test_tiles_from_uniq_accepts_sequence():
    """The helper accepts any array-like, not just numpy arrays."""
    uniq, expected = zip(_uniq_and_range(0, 0), _uniq_and_range(5, 100))
    assert list(Tile.tiles_from_uniq(list(uniq))) == list(expected)
