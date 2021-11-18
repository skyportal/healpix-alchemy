"""SQLAlchemy functions."""
from sqlalchemy import func as _func

from .types import Tile as _Tile


def union(tiles):
    return _func.unnest(_func.range_agg(tiles), type_=_Tile)
