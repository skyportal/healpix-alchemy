"""SQLAlchemy sample data for unit tests.

Notes
-----
We use the psycopg ``copy`` rather than SQLAlchemy for fast insertion.

"""

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord, uniform_spherical_random_surface
from mocpy import MOC

from healpix_alchemy.constants import HPX, LEVEL, PIXEL_AREA
from healpix_alchemy.types import Tile

from .models import Field, FieldTile, Galaxy, Skymap, SkymapTile

(RANDOM_GALAXIES_SEED, RANDOM_FIELDS_SEED, RANDOM_SKY_MAP_SEED) = (
    np.random.SeedSequence(12345).spawn(3)
)


def get_ztf_footprint_corners():
    """Return the corner offsets of the ZTF footprint.

    Notes
    -----
    This polygon is smaller than the spatial extent of the true ZTF field of
    view, but has approximately the same area because the real ZTF field of
    view has chip gaps.

    For the real ZTF footprint, use the region file
    https://github.com/skyportal/skyportal/blob/main/data/ZTF_Region.reg.
    """
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
        monkeypatch.setattr(np, "random", np.random.default_rng(seed))
        return uniform_spherical_random_surface(n)


def get_random_galaxies(n, cursor):
    points = SkyCoord(get_random_points(n, RANDOM_GALAXIES_SEED))
    hpx = HPX.skycoord_to_healpix(points)

    with cursor.copy(f"COPY {Galaxy.__tablename__} (hpx) FROM STDIN") as copy:
        copy.write("\n".join(f"{i}" for i in hpx))

    return points


def get_random_fields(n, cursor):
    centers = SkyCoord(get_random_points(n, RANDOM_FIELDS_SEED))
    footprints = get_footprints_grid(*get_ztf_footprint_corners(), centers)
    mocs = [MOC.from_polygon_skycoord(footprint) for footprint in footprints]

    with cursor.copy(f"COPY {Field.__tablename__} FROM STDIN") as copy:
        copy.write("\n".join(f"{i}" for i in range(len(mocs))))

    with cursor.copy(f"COPY {FieldTile.__tablename__} FROM STDIN") as copy:
        copy.write(
            "\n".join(
                f"{i}\t{hpx}"
                for i, moc in enumerate(mocs)
                for hpx in Tile.tiles_from(moc)
            )
        )

    return mocs


def get_random_sky_map(n, cursor):
    rng = np.random.default_rng(RANDOM_SKY_MAP_SEED)
    # Make a randomly subdivided sky map
    npix = HPX.npix
    tiles = np.arange(0, npix + 1, 4**LEVEL).tolist()
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

    with cursor.copy(f"COPY {Skymap.__tablename__} FROM STDIN") as copy:
        copy.write("1")

    with cursor.copy(f"COPY {SkymapTile.__tablename__} FROM STDIN") as copy:
        copy.write(
            "\n".join(
                f"1\t[{lo},{hi})\t{p}"
                for lo, hi, p in zip(tiles[:-1], tiles[1:], probdensity)
            )
        )

    return tiles, probdensity
