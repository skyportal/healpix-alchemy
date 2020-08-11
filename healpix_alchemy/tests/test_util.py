import pytest
from sqlalchemy.ext.declarative import declared_attr

from ..util import InheritTableArgs


@pytest.mark.parametrize('base_table_args,expected_table_args', [
    [None, (1, {'bar': 2})],
    [[], (1, {'bar': 2})],
    [{}, (1, {'bar': 2})],
    [[0], (0, 1, {'bar': 2})],
    [[{'foo': 1}], (1, {'foo': 1, 'bar': 2})],
    [[0, {'foo': 1}], (0, 1, {'foo': 1, 'bar': 2})],
])
def test_inherit_table_args(base_table_args, expected_table_args):

    class Base:
        if base_table_args is not None:
            __table_args__ = base_table_args

    class Derived(InheritTableArgs, Base):
        @declared_attr
        def __table_args__(cls):
            *args, kwargs = super().__table_args__
            args = (*args, 1)
            kwargs = {**kwargs, 'bar': 2}
            return (*args, kwargs)

    assert Derived.__table_args__ == expected_table_args
