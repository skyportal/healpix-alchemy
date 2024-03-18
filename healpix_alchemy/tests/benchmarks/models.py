"""SQLAlchemy ORM models for unit tests."""
import sqlalchemy as sa
from sqlalchemy import orm

from ...types import Point, Tile


@orm.as_declarative()
class Base:

    @orm.declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class Galaxy(Base):
    id = sa.Column(sa.Integer, primary_key=True)
    hpx = sa.Column(Point, index=True, nullable=False)


class Field(Base):
    id = sa.Column(sa.Integer, primary_key=True)


class FieldTile(Base):
    id = sa.Column(sa.ForeignKey(Field.id), primary_key=True, index=True)
    hpx = sa.Column(Tile, primary_key=True, index=True)


class Skymap(Base):
    id = sa.Column(sa.Integer, primary_key=True)


class SkymapTile(Base):
    id = sa.Column(sa.ForeignKey(Skymap.id), primary_key=True)
    hpx = sa.Column(Tile, primary_key=True, index=True)
    probdensity = sa.Column(sa.Float, nullable=False)


class TileList(Base):
    hpx = sa.Column(Tile, primary_key=True, index=True)
