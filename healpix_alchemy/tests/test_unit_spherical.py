from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer

from ..unit_spherical import (UnitSphericalCoordinate,
                              HasUnitSphericalCoordinate)


Base = declarative_base()


class Points(HasUnitSphericalCoordinate, Base):
    __tablename__ = 'points'
    id = Column(Integer, primary_key=True)


def test_unit_spherical(postgresql_engine):
    Base.metadata.create_all(postgresql_engine)
