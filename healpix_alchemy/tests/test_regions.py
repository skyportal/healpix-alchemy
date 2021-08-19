import re

from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy import units as u
from astropy.utils.data import get_readable_fileobj
from astropy_healpix import level_ipix_to_uniq
from mocpy import MOC
import numpy as np
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .. import Region, Tile


Base = declarative_base()


class Field(Region, Base):
    __tablename__ = 'fields'

    field_id = Column(
        Integer,
        primary_key=True)

    tile_class = lambda: FieldTile  # noqa: E731

    tiles = relationship("FieldTile")


class FieldTile(Tile, Base):
    __tablename__ = 'fieldtiles'

    instrument_field_id = Column(
        ForeignKey('fields.field_id', ondelete="CASCADE"),
        nullable=False,
        doc='Instrument Field ID',
    )

    field = relationship(
        "Field",
        foreign_keys=instrument_field_id
    )


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
    return SkyCoord(lon, lat, frame=offsets[:, np.newaxis].skyoffset_frame())


def test_fields(request, session, engine):
    """Generate ZTF fields and ingest them."""
    Base.metadata.create_all(engine)

    url = ('https://github.com/ZwickyTransientFacility/ztf_information/raw/'
           'master/field_grid/ZTF_Fields.txt')
    with get_readable_fileobj(url, show_progress=False) as f:
        first_line, *lines = f
        names = re.split(r'\s\s+', first_line.lstrip('%').strip())
        table = Table.read(lines, format='ascii', names=names)
    # keep subset of fields for speed
    table = table[::100]

    lon, lat = get_ztf_footprint_corners()
    centers = SkyCoord(table['RA'] * u.deg, table['Dec'] * u.deg)
    vertices = get_footprints_grid(lon, lat, centers)

    mocs = [MOC.from_polygon_skycoord(verts) for verts in vertices]

    fields = [Field.from_moc(moc, field_id=int(field_id))
              for field_id, moc in zip(table['ID'], mocs)]
    for field in fields:
        session.add(field)
    session.commit()

    fields = session.query(Field).all()
    assert len(fields) == 18


def test_tile(engine):
    """Generate an example Tile and confirm index calculation."""
    Base.metadata.create_all(engine)

    LEVEL = MOC.HPY_MAX_NORDER

    level, ipix = 3, 12
    value = level_ipix_to_uniq(level, ipix)
    shift = 2 * (LEVEL - level)
    nested_lo = int(ipix << shift)
    nested_hi = int(((ipix + 1) << shift) - 1)

    tile = Tile(uniq=value)
    assert tile.nested_lo == nested_lo
    assert tile.nested_hi == nested_hi
    assert tile.uniq == value
