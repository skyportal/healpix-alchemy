"""SQLAlchemy sample data for unit tests.

Notes
-----
We use the psycopg2 ``copy_from`` rather than SQLAlchemy for fast insertion.

"""
import io

from astropy.coordinates import SkyCoord, uniform_spherical_random_surface
from astropy import units as u
from mocpy import MOC
import numpy as np
import pytest

from ...constants import HPX, LEVEL, PIXEL_AREA
from ...types import Tile
from .models import Galaxy, Field, FieldTile, Skymap, SkymapTile

(
    RANDOM_GALAXIES_SEED,
    RANDOM_FIELDS_SEED,
    RANDOM_SKY_MAP_SEED
) = np.random.SeedSequence(12345).spawn(3)


def get_ztf_footprint_corners():
    """Return the corner offsets of the ZTF footprint."""
    x = 6.86 / 2
    return [-x, +x, +x, -x] * u.deg, [-x, -x, +x, +x] * u.deg


def get_footprints_grid(lon, lat, offsets):
    """Get a grid of footprints for an equatorial-mount telescope.

    Parameters
    ----------
    lon : astropy.units.Quantity
        Longitudes of footprint vertices at the standard pointing.
        Should be an array of length N.
    lat : astropy.units.Quantity
        Latitudes of footprint vertices at the standard pointing.
        Should be an array of length N.
    offsets : astropy.coordinates.SkyCoord
        Pointings for the field grid.
        Should have length M.

    Returns
    -------
    astropy.coordinates.SkyCoord
        Footprints with dimensions (M, N).
    """
    lon = np.repeat(lon[np.newaxis, :], len(offsets), axis=0)
    lat = np.repeat(lat[np.newaxis, :], len(offsets), axis=0)
    result = SkyCoord(lon, lat, frame=offsets[:, np.newaxis].skyoffset_frame())
    return result.icrs


def get_random_points(n, seed):
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(np, 'random', np.random.default_rng(seed))
        return uniform_spherical_random_surface(n)


def get_random_galaxies(n, cursor):
    points = SkyCoord(get_random_points(n, RANDOM_GALAXIES_SEED))
    hpx = HPX.skycoord_to_healpix(points)

    f = io.StringIO('\n'.join(f'{i}' for i in hpx))
    cursor.copy_from(f, Galaxy.__tablename__, columns=('hpx',))

    return points


def get_random_fields(n, cursor):
    centers = SkyCoord(get_random_points(n, RANDOM_FIELDS_SEED))
    footprints = get_footprints_grid(*get_ztf_footprint_corners(), centers)
    mocs = [MOC.from_polygon_skycoord(footprint) for footprint in footprints]

    f = io.StringIO('\n'.join(f'{i}' for i in range(len(mocs))))
    cursor.copy_from(f, Field.__tablename__)

    f = io.StringIO(
        '\n'.join(
            f'{i}\t{hpx}'
            for i, moc in enumerate(mocs) for hpx in Tile.tiles_from(moc)
        )
    )
    cursor.copy_from(f, FieldTile.__tablename__)

    return mocs


def get_random_sky_map(n, cursor):
    rng = np.random.default_rng(RANDOM_SKY_MAP_SEED)
    # Make a randomly subdivided sky map
    npix = HPX.npix
    tiles = np.arange(0, npix + 1, 4 ** LEVEL).tolist()
    while len(tiles) < n:
        i = rng.integers(len(tiles))
        lo = 0 if i == 0 else tiles[i - 1]
        hi = tiles[i]
        diff = (hi - lo) // 4
        if diff == 0:
            continue
        tiles.insert(i, hi - diff)
        tiles.insert(i, hi - 2 * diff)
        tiles.insert(i, hi - 3 * diff)

    probdensity = rng.uniform(0, 1, size=len(tiles) - 1)
    probdensity /= np.sum(np.diff(tiles) * probdensity) * PIXEL_AREA

    f = io.StringIO('1')
    cursor.copy_from(f, Skymap.__tablename__)

    f = io.StringIO(
        '\n'.join(
            f'1\t[{lo},{hi})\t{p}'
            for lo, hi, p in zip(tiles[:-1], tiles[1:], probdensity)
        )
    )
    cursor.copy_from(f, SkymapTile.__tablename__)

    return tiles, probdensity
