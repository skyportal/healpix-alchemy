# HEALPix Alchemy

The `healpix_alchemy` Python package extends [SQLAlchemy] will provide spatial
indexing for astronomical sky coordinates, regions, and raster images (e.g.
LIGO/Virgo and Fermi probability sky maps) in a relational database. It does
not rely on any database extensions.

This package is a work in progress. Initially, `healpix_alchemy` focuses on
spatial indexing of point clouds while we work out the SQLAlchemy abstraction
design. Once this is mature, we will incorporate the raster indexing strategies
from https://github.com/growth-astro/healpix-intersection-example.

## Installation

You can install `healpix_alchemy` the Python Package Index:

    $ pip install healpix-alchemy

Or from GitHub:

    $ pip install git+https://github.com/skyportal/healpix-alchemy

## Usage

```python
from healpix_alchemy.point import HasPoint, Point
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Create two tables Catalog1 and Catalog2 that both have spherical coordinates.

class Catalog1(HasPoint, Base):
    __tablename__ = 'catalog1'
    id = Column(Integer, primary_key=True)


class Catalog2(HasPoint, Base):
    __tablename__ = 'catalog2'
    id = Column(Integer, primary_key=True)


...

# Populate Catalog1 and Catalog2 tables with some sample data...
session.add(Catalog1(id=0, point=Point(ra=320.5, dec=-23.5)))
...
session.add(Catalog2(id=0, point=Point(ra=18.1, dec=18.3)))
...
session.commit()


# Cross-match the two tables.
separation = 1  # separation in degrees
query = session.query(
    Catalog1.id, Catalog2.id
).join(
    Catalog2,
    Catalog1.point.within(Catalog2.point, separation)
).order_by(
    Catalog1.id, Catalog2.id
)
for row in query:
    ...  # do something with the query results
```

[SQLAlchemy]: https://www.sqlalchemy.org
