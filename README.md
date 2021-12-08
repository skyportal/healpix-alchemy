[![PyPI Status](https://img.shields.io/pypi/v/healpix-alchemy)](https://pypi.org/project/healpix-alchemy/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/skyportal/healpix-alchemy/build-and-test)](https://github.com/skyportal/healpix-alchemy/actions)
[![codecov](https://codecov.io/gh/skyportal/healpix-alchemy/branch/main/graph/badge.svg?token=T34O35OM0V)](https://codecov.io/gh/skyportal/healpix-alchemy)

# HEALPix Alchemy

The `healpix_alchemy` Python package is an extension for the [SQLAlchemy]
object relational mapper. It adds region and image arithmetic to [PostgreSQL]
(version 14 and newer) databases. It accelerates queries between point clouds,
regions, and images (sometimes known in the geospatial community as rasters) by
storing [multi-order] [HEALPix] indices in PostgreSQL's [range types].

The `healpix_alchemy` project is designed for astronomy applications,
particularly for cross-matching galaxy catalogs, observation footprints, and
all-sky images like [gravitational-wave probability sky maps] or even dust
maps. However, it could be used in any context in which geometry is embedded on
a unit sphere.

`healpix_alchemy` is lean and minimalist because it leverages several existing
projects: it consists of little more than a few lines of glue code to bind
together [MOCPy], [SQLAlchemy], and PostgreSQL's [range types].

`healpix_alchemy` serves a purpose similar to full-featured astronomy-focused
spatial extensions like [Q3C], [H3C], and [pg_healpix], and geospatial
extensions like [PgSphere] and [PostGIS]. What sets `healpix_alchemy` apart
from these is that it is written in pure Python and requires no server-side
database extensions. Consequently, `healpix_alchemy` can be used with managed
PostgreSQL databases in the cloud like [Amazon RDS] and [Google Cloud SQL].

[2MASS Redshift Survey]: https://lweb.cfa.harvard.edu/~dfabricant/huchra/2mass/
[Aladin]: https://aladin.u-strasbg.fr
[Amazon RDS]: https://aws.amazon.com/rds/
[astropy.coordinates.SkyCoord]: https://docs.astropy.org/en/stable/api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord
[astropy.units.Quantity]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity
[custom column types]: https://docs.sqlalchemy.org/en/14/core/custom_types.html
[Google Cloud SQL]: https://cloud.google.com/sql
[Górski et al. (2005)]: https://doi.org/10.1086/427976
[gravitational-wave probability sky maps]: https://emfollow.docs.ligo.org/userguide/tutorial/skymaps.html
[GW200115_042309]: https://doi.org/10.3847/2041-8213/ac082e
[H3C]: http://cdsarc.u-strasbg.fr/h3c
[HEALPix]: https://healpix.sourceforge.io
[hierarchical progressive surveys (HiPS)]: https://www.ivoa.net/documents/HiPS/
[ICRS]: https://docs.astropy.org/en/stable/api/astropy.coordinates.builtin_frames.ICRS.html#astropy.coordinates.builtin_frames.ICRS
[ligo-segments]: https://lscsoft.docs.ligo.org/ligo-segments/
[MOCPy documentation]: https://cds-astro.github.io/mocpy/
[MOCPy]: https://github.com/tboch/mocpy
[multi-order coverage (MOC)]: https://ivoa.net/documents/MOC/
[multi-order]: https://doi.org/10.1051/0004-6361/201526549
[official Poetry installation instructions]: https://python-poetry.org/docs/#installation
[pg_healpix]: https://github.com/segasai/pg_healpix
[PgSphere]: https://pgsphere.github.io
[pip]: https://pip.pypa.io/
[Poetry]: https://python-poetry.org/
[PostGIS]: https://postgis.net
[PostgreSQL]: https://www.postgresql.org
[pyranges]: https://github.com/biocore-ntnu/pyranges
[pytest]: https://pytest.org/
[Q3C]: https://github.com/segasai/q3c
[range types]: https://www.postgresql.org/docs/current/rangetypes.html
[S200115j]: https://gracedb.ligo.org/superevents/S200115j/view/
[Singer & Price (2015)]: https://doi.org/10.1103/PhysRevD.93.024013
[SQLAlchemy bulk insertion]: https://docs.sqlalchemy.org/en/14/orm/persistence_techniques.html#bulk-operations
[SQLAlchemy]: https://www.sqlalchemy.org
[UNIQ]: https://healpix.sourceforge.io/doc/html/intro_Geometric_Algebraic_Propert.htm#SECTION420
[Zwicky Transient Facility]: https://www.ztf.caltech.edu

## Theory of operation

### HEALPix basics

[HEALPix] is a scheme for subdividing and indexing the unit sphere, originally
described by [Górski et al. (2005)]. Although it was originally designed for
cosmic microwave background analysis, it has found many uses in astronomy,
particularly through [multi-order coverage (MOC)] maps and
[hierarchical progressive surveys (HiPS)] used extensively in the [Aladin]
astronomical information system. It is also used by LIGO and Virgo to store and
communicate [gravitational-wave probability sky maps].

HEALPix can be thought of as a tree. At the lowest resolution, level 0, HEALPix
subdivides the sphere into 12 equal-area base tiles, assigned integer indices
0 through 11. At level 1, each of the 12 base tiles is subdivided into 4 tiles.
Every subsequent level divides each of the preceding level's tiles into 4 new
tiles. At a given level, each of the base pixels has been divided into
4<sup>_level_</sup> pixels (_nside_ = 2<sup>_level_</sup> pixels on each side).
Thus there are _npix_ = 12×4<sup>_level_</sup> pixels at a given resolution,
assigned integer indices from 0 through (_npix_-1). This is called the NESTED
indexing scheme. (There is also a RING indexing scheme in which the indices
advance from east to west and then from north to south.)

A HEALPix tile, a node in the HEALPix tree, is fully addressed by three pieces
of information: the indexing scheme (RING or NESTED), the resolution level
(_level_ or equivalently _nside_), and the pixel index (_ipix_, an integer
between 0 and _npix_-1).

The image below, reproduced from https://healpix.jpl.nasa.gov, illustrates the
first 4 levels of refinement of a HEALPix grid.

![The first four levels of HEALPix subdivision of the unit sphere](https://healpix.jpl.nasa.gov/images/healpixGridRefinement.jpg)

### HEALPix interval sets

A region on the sphere can be encoded by a collection of disjoint HEALPix
tiles, potentially at a mix of different resolution levels. Typically, large
low-resolution tiles are used on the interior of the region, and small
high-resolution tiles are used on the boundary. This is called a
[multi-order coverage (MOC)] map. An example, reproduced from the
[MOCPy documentation], is shown below.

![An example HEALPix multi-order coverage map](https://cds-astro.github.io/mocpy/_images/plot_SDSS_r.png)

Much like MOCs, LIGO/Virgo/KAGRA gravitational-wave probability sky maps are
stored as multi-resolution HEALPix data sets, but with a vector of
floating-point values attached to each tile. A multi-order refinement mesh from
an example sky map is shown below, reproduced from [Singer & Price (2015)].

![Example multi-order refinement mesh from a gravitational-wave probability sky map](https://emfollow.docs.ligo.org/userguide/_images/healpix-adaptive-mesh.svg)

[Reinecke & Hivon (2015)][multi-order] introduced HEALPix interval sets as an
alternative encoding of MOCs that enables fast and simple unions,
intersections, and queries. In an interval set, each HEALPix tile is described
by the interval of pixel indices at some very high resolution
_level_<sub>max</sub> that are descendents of that tile. In an interval set, a
region is encoded as a disjoint collection of such intervals. A tile with a
NESTED address given by (_level_, _ipix_) may be described as the half-open
interval

[_ipix_ 4<sup>_level_<sub>max</sub> - _level_</sup>,
(_ipix_ + 1) 4<sup>_level_<sub>max</sub> - _level_</sup>).

We use _level_<sub>max</sub> = 29 because this is the highest resolution at
which pixel indices can be stored in a signed 64-bit integer. At this
resolution, each pixel is scarcely 0.4 milliarcseconds across.

The interval set representation is adventageous because there are simple and
fast algorithms for interval arithmetic and set operations. Interval analysis
appears in a suprising variety of scientific contexts from [genomics][pyranges]
to [gravitational wave data quality][ligo-segments]. Because of the many
business applications of interval arithmetic, intervals are also supported in
the [PostgreSQL] database through its [range types].

### Spatial primitives in `healpix_alchemy`

The `healpix_alchemy` package provides two [custom column types] for
[SQLAlchemy]:

#### `healpix_alchemy.Point`

This class represents a point. A column of this type could store the positions
of galaxies in a catalog. Under the hood, it is just a `BIGINT`.

Wherever you need to bind a Python value to a `healpix_alchemy.Point`, you may
provide any one of the following:
* an instance of [astropy.coordinates.SkyCoord]
* a sequence of two [astropy.units.Quantity] instances with angle units, which
  will be interpreted as the right ascension and declination of the point in
  the [ICRS] frame
* an integer representing the HEALPix NESTED index of the point at
  _level_ = _level_<sub>max</sub>

#### `healpix_alchemy.Tile`

This class represents a HEALPix tile. A table containing a column of this type
and a foreign key could store MOCs or gravitational-wave probability maps.
Under the hood, it is just an `INT8RANGE`.

Wherever you need to bind a Python value to a `healpix_alchemy.Tile`, you may
provide any one of the following:
* A single integer which will be interpreted as the address of the tile in the
  [UNIQ] HEALPix indexing scheme
* A sequence of two integers, which will be interpreted as the lower and upper
  bounds of the right-half-open pixel index interval at
  _level_ = _level_<sub>max</sub>
* A string like `'[1234,5678)'`

## Installation

You can install `healpix_alchemy` from the Python Package Index using [pip]:

```console
$ pip install healpix-alchemy
```

## Development Installation

Contributions are welcome! This package uses the [Poetry] packaging and
dependency tool and [pytest] for unit tests. To install `healpix_alchemy` in a
development environment, follow these instructions.

1.  Install [Poetry] by following the
    [official Poetry installation instructions].

2.  Clone this repository:

    ```console
    $ git clone https://github.com/skyportal/healpix-alchemy.git
    $ cd healpix-alchemy
    ```

3.  Initialize the Poetry-managed virtual environment with `healpix_alchemy`
    and all of its dependencies installed by running this command:

    ```console
    $ poetry install
    ```

    Now, you can enter a shell inside the virtual environment by running:

    ```console
    $ poetry shell
    ```

4.  To run the test suite, including the examples in this README file, run this
    command inside the Poetry shell:

    ```console
    $ pytest
    ```

## Example

First, some imports:

```pycon
>>> import sqlalchemy as sa
>>> from sqlalchemy.ext.declarative import as_declarative, declared_attr
>>> import healpix_alchemy as ha

```

### Set up tables

This example will use the SQLAlchemy declarative extension for describing table
schema using Python classes.

SQLAlchemy needs to know the name for each table. You can provide the name by
setting the `__tablename__` attribute in each model class, or you can
create a base class that generates the table name automatically from the class
name.

```pycon
>>> @as_declarative()
... class Base:
...
...     @declared_attr
...     def __tablename__(cls):
...         return cls.__name__.lower()

```

Each row of the `Galaxy` table represents a point in a catalog:

```pycon
>>> class Galaxy(Base):
...     id = sa.Column(sa.Text, primary_key=True)
...     hpx = sa.Column(ha.Point, index=True, nullable=False)

```

Each row of the `Field` table represents a ZTF field:

```pycon
>>> class Field(Base):
...     id = sa.Column(sa.Integer, primary_key=True)
...     tiles = sa.orm.relationship(lambda: FieldTile)

```

Each row of the `FieldTile` table represents a multi-resolution HEALPix tile
that is contained within the corresponding field. There is a one-to-many
mapping between `Field` and `FieldTile`.

```pycon
>>> class FieldTile(Base):
...     id = sa.Column(sa.ForeignKey(Field.id), primary_key=True)
...     hpx = sa.Column(ha.Tile, primary_key=True, index=True)

```

Each row of the `Skymap` table represents a LIGO/Virgo HEALPix
localization map.

```pycon
>>> class Skymap(Base):
...     id = sa.Column(sa.Integer, primary_key=True)
...     tiles = sa.orm.relationship(lambda: SkymapTile)

```

Each row of the `SkymapTile` table represents a multi-resolution HEALPix
tile within a LIGO/Virgo localization map. There is a one-to-many mapping
between `Skymap` and `SkymapTile`.

```pycon
>>> class SkymapTile(Base):
...     id = sa.Column(sa.ForeignKey(Skymap.id), primary_key=True)
...     hpx = sa.Column(ha.Tile, primary_key=True, index=True)
...     probdensity = sa.Column(sa.Float, nullable=False)

```

Finally, connect to the database, create all the tables, and start a session.

```pycon
>>> engine = sa.create_engine('postgresql://user:password@host/database')
>>> Base.metadata.create_all(engine)
>>> session = sa.orm.Session(engine)

```

### Populate with sample data

Load the [2MASS Redshift Survey] into the `Galaxy` table. This catalog contains
44599 galaxies.

It may take up to a minute for this to finish. Advanced users may speed this up
significantly by vectorizing the conversion from `SkyCoord` to HEALPix indices
and using [SQLAlchemy bulk insertion].

```pycon
>>> from astropy.coordinates import SkyCoord
>>> from astroquery.vizier import Vizier
>>> vizier = Vizier(columns=['SimbadName', 'RAJ2000', 'DEJ2000'], row_limit=-1)
>>> data, = vizier.get_catalogs('J/ApJS/199/26/table3')
>>> data['coord'] = SkyCoord(data['RAJ2000'], data['DEJ2000'])
>>> for row in data:
...     session.add(Galaxy(id=row['SimbadName'], hpx=row['coord']))
>>> session.commit()

```

Load the footprints of the [Zwicky Transient Facility] fields into the `Field`
and `FieldTile` tables.

It may take up to a minute for this to finish. Advanced users may speed this up
significantly by using [SQLAlchemy bulk insertion].

```pycon
>>> from astropy.table import Table
>>> from astropy.coordinates import SkyCoord
>>> from astropy import units as u
>>> url = 'https://raw.githubusercontent.com/ZwickyTransientFacility/ztf_information/master/field_grid/ztf_field_corners.csv'
>>> for row in Table.read(url):
...     field_id = int(row['field'])
...     corners = SkyCoord(row['ra1', 'ra2', 'ra3', 'ra4'],
...                        row['dec1', 'dec2', 'dec3', 'dec4'],
...                        unit=u.deg)
...     tiles = [FieldTile(hpx=hpx) for hpx in ha.Tile.tiles_from(corners)]
...     session.add(Field(id=field_id, tiles=tiles))
>>> session.commit()

```

Load a sky map for LIGO/Virgo event [GW200115_042309] ([S200115j]) into the
`Skymap` and `SkymapTile` tables.

```pycon
>>> url = 'https://gracedb.ligo.org/apiweb/superevents/S200115j/files/bayestar.multiorder.fits'
>>> data = Table.read(url)
>>> tiles = [SkymapTile(hpx=row['UNIQ'], probdensity=row['PROBDENSITY']) for row in data]
>>> session.add(Skymap(id=1, tiles=tiles))
>>> session.commit()

```

### Sample Queries

#### What is the area of each field?

```pycon
>>> query = sa.select(
...     FieldTile.id, sa.func.sum(FieldTile.hpx.area)
... ).group_by(
...     FieldTile.id
... ).limit(
...     5
... )
>>> for id, area in session.execute(query):
...     print(f'Field {id} has area {area:.3g} sr')
Field 199 has area 0.0174 sr
Field 200 has area 0.0174 sr
Field 201 has area 0.0174 sr
Field 202 has area 0.0174 sr
Field 203 has area 0.0174 sr

```

#### How many galaxies are in each field?

```pycon
>>> count = sa.func.count(Galaxy.id)
>>> query = sa.select(
...     FieldTile.id, count
... ).filter(
...     FieldTile.hpx.contains(Galaxy.hpx)
... ).group_by(
...     FieldTile.id
... ).order_by(
...     count.desc()
... ).limit(
...     5
... )
>>> for id, n in session.execute(query):
...     print(f'Field {id} contains {n} galaxies')
Field 1739 contains 343 galaxies
Field 699 contains 336 galaxies
Field 700 contains 311 galaxies
Field 225 contains 303 galaxies
Field 1740 contains 289 galaxies

```

#### What is the probability density at the position of each galaxy?

```pycon
>>> query = sa.select(
...     Galaxy.id, SkymapTile.probdensity
... ).filter(
...     SkymapTile.id == 1,
...     SkymapTile.hpx.contains(Galaxy.hpx)
... ).order_by(
...     SkymapTile.probdensity.desc()
... ).limit(
...     5
... )
>>> for id, p in session.execute(query):
...     print(f'{id} has prob. density {p:.5g}/sr')
2MASX J02532153+0632222 has prob. density 20.701/sr
2MASX J02530482+0555431 has prob. density 20.695/sr
2MASX J02533119+0628252 has prob. density 20.669/sr
2MASX J02524584+0639206 has prob. density 20.656/sr
2MASX J02534120+0615562 has prob. density 20.567/sr

```

#### What is the probability contained within each field?

```pycon
>>> area = (FieldTile.hpx * SkymapTile.hpx).area
>>> prob = sa.func.sum(SkymapTile.probdensity * area)
>>> query = sa.select(
...     FieldTile.id, prob
... ).filter(
...     SkymapTile.id == 1,
...     FieldTile.hpx.overlaps(SkymapTile.hpx)
... ).group_by(
...     FieldTile.id
... ).order_by(
...     prob.desc()
... ).limit(
...     5
... )
>>> for id, prob in engine.execute(query):
...     print(f'Field {id} probability is {prob:.3g}')
Field 1499 probability is 0.165
Field 1446 probability is 0.156
Field 452 probability is 0.154
Field 505 probability is 0.0991
Field 401 probability is 0.0962

```

#### What is the combined area of fields 1000 through 2000?

In the next two examples, we introduce `healpix_alchemy.func.union()` which
finds the union of a set of tiles. Because it is an aggregate function, it
should generally be used in a subquery.

```pycon
>>> union = sa.select(
...     ha.func.union(FieldTile.hpx).label('hpx')
... ).filter(
...     FieldTile.id.between(1000, 2000)
... ).subquery()
>>> query = sa.select(
...     sa.func.sum(union.columns.hpx.area)
... )
>>> result = session.execute(query).scalar_one()
>>> print(f'{result:.3g} sr')
9.33 sr

```

#### What is the integrated probability contained within fields 1000 through 2000?

```pycon
>>> union = sa.select(
...     ha.func.union(FieldTile.hpx).label('hpx')
... ).filter(
...     FieldTile.id.between(1000, 2000)
... ).subquery()
>>> prob = sa.func.sum(SkymapTile.probdensity * (union.columns.hpx * SkymapTile.hpx).area)
>>> query = sa.select(
...     prob
... ).filter(
...     SkymapTile.id == 1,
...     union.columns.hpx.overlaps(SkymapTile.hpx)
... )
>>> result = session.execute(query).scalar_one()
>>> print(f'{result:.3g}')
0.837

```

#### What is the area of the 90% credible region?

```pycon
>>> cum_area = sa.func.sum(
...     SkymapTile.hpx.area
... ).over(
...     order_by=SkymapTile.probdensity.desc()
... ).label(
...     'cum_area'
... )
>>> cum_prob = sa.func.sum(
...     SkymapTile.probdensity * SkymapTile.hpx.area
... ).over(
...     order_by=SkymapTile.probdensity.desc()
... ).label(
...     'cum_prob'
... )
>>> subquery = sa.select(
...     cum_area,
...     cum_prob
... ).filter(
...     SkymapTile.id == 1
... ).subquery()
>>> query = sa.select(
...     sa.func.max(subquery.columns.cum_area)
... ).filter(
...     subquery.columns.cum_prob <= 0.9
... )
>>> result = session.execute(query).scalar_one()
>>> print(f'{result:.3g} sr')
0.277 sr

```

#### Which galaxies are within the 90% credible region?

```pycon
>>> cum_prob = sa.func.sum(
...     SkymapTile.probdensity * SkymapTile.hpx.area
... ).over(
...     order_by=SkymapTile.probdensity.desc()
... ).label(
...     'cum_prob'
... )
>>> subquery1 = sa.select(
...     SkymapTile.probdensity,
...     cum_prob
... ).filter(
...     SkymapTile.id == 1
... ).subquery()
>>> min_probdensity = sa.select(
...     sa.func.min(subquery1.columns.probdensity)
... ).filter(
...     subquery1.columns.cum_prob <= 0.9
... ).scalar_subquery()
>>> query = sa.select(
...     Galaxy.id
... ).filter(
...     SkymapTile.id == 1,
...     SkymapTile.hpx.contains(Galaxy.hpx),
...     SkymapTile.probdensity >= min_probdensity
... ).limit(
...     5
... )
>>> for galaxy_id, in session.execute(query):
...     print(galaxy_id)
2MASX J02424077-0000478
2MASX J02352772-0921216
2MASX J02273746-0109226
2MASX J02414523+0026354
2MASX J20095408-4822462

```
