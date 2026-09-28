"""SQLAlchemy functions."""

from typing import Any

import sqlalchemy as sa
from sqlalchemy import func as _func
from sqlalchemy.sql.functions import Function

from .types import Tile as _Tile


def union(tiles: sa.ColumnElement[Any]) -> Function[str]:
    return _func.unnest(_func.range_agg(tiles), type_=_Tile)
