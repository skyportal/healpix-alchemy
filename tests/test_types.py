"""Unit tests for healpix_alchemy.types that do not require a database."""

import numpy as np
import pytest

from healpix_alchemy.constants import LEVEL
from healpix_alchemy.types import Tile


def _uniq_and_range(level, ipix):
    """Construct a UNIQ index and its expected ``[lo,hi)`` range string.

    This is the definition of the UNIQ (NUNIQ) encoding,
    ``uniq = ipix + 4 ** (level + 1)``, used as an independent ground truth.
    We deliberately do not use ``astropy_healpix.uniq_to_level_ipix`` as the
    oracle because it loses precision and mis-decodes the last pixel at
    levels >= 24 (where ``4 ** (level + 2)`` exceeds 2 ** 52).
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


def test_tile_bind_uniq_scalar(uniq_and_expected):
    """Binding a single UNIQ integer decodes to the correct range."""
    tile = Tile()
    uniq, expected = uniq_and_expected
    for value, want in zip(uniq.tolist(), expected):
        assert tile.process_bind_param(value, None) == want


def test_tile_bind_uniq_numpy_scalar(uniq_and_expected):
    """A numpy integer binds identically to a Python int."""
    tile = Tile()
    uniq, expected = uniq_and_expected
    for value, want in zip(uniq, expected):
        assert tile.process_bind_param(value, None) == want


def test_tile_bind_uniq_boundary_pixel():
    """The last pixel at high levels decodes correctly (regression test).

    astropy_healpix.uniq_to_level_ipix mis-decodes these to ipix == -1.
    """
    tile = Tile()
    for level in range(LEVEL + 1):
        npix = 12 * 4**level
        uniq, want = _uniq_and_range(level, npix - 1)
        assert tile.process_bind_param(uniq, None) == want


def test_tiles_from_uniq_matches_scalar(uniq_and_expected):
    """The vectorized helper agrees with the per-element bind path."""
    tile = Tile()
    uniq, _ = uniq_and_expected
    expected = [tile.process_bind_param(int(value), None) for value in uniq]
    assert list(Tile.tiles_from_uniq(uniq)) == expected


def test_tiles_from_uniq_accepts_sequence():
    """The helper accepts any array-like, not just numpy arrays."""
    uniq, expected = zip(_uniq_and_range(0, 0), _uniq_and_range(5, 100))
    assert list(Tile.tiles_from_uniq(list(uniq))) == list(expected)


def test_tile_bind_sequence_and_string_passthrough():
    """Non-UNIQ inputs keep their existing behavior."""
    tile = Tile()
    assert tile.process_bind_param((10, 20), None) == "[10,20)"
    assert tile.process_bind_param("[10,20)", None) == "[10,20)"
