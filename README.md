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
from healpix_alchemy.unit_spherical import (UnitSphericalCoordinate,
                                            HasUnitSphericalCoordinate)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Create two tables Point1 and Point2 that both have spherical coordinates.

class Point1(HasUnitSphericalCoordinate, Base):
    __tablename__ = 'points1'
    id = Column(Integer, primary_key=True)


class Point2(HasUnitSphericalCoordinate, Base):
    __tablename__ = 'points2'
    id = Column(Integer, primary_key=True)


...

# Populate Point1 and Point2 tables with some sample data...
session.add(Point1(id=0, coordinate=UnitSphericalCoordinate(ra=320.5, dec=-23.5)))
...
session.add(Point2(id=0, coordinate=UnitSphericalCoordinate(ra=18.1, dec=18.3)))
...
session.commit()


# Cross-match the two tables.
separation = 1  # separation in degrees
query = session.query(
    Point1.id, Point2.id
).join(
    Point2,
    Point1.coordinate.within(Point2.coordinate, separation)
).order_by(
    Point1.id, Point2.id
)
for row in query:
    ...  # do something with the query results
```

[SQLAlchemy]: https://www.sqlalchemy.org
