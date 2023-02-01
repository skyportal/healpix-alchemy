"""SQLAlchemy temporary tables.

Inspired by https://github.com/sqlalchemy/sqlalchemy/wiki/Views
"""
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import TableClause

from uuid import uuid4

__all__ = ('temporary_table',)


class CreateTemporaryTable(DDLElement):

    inherit_cache = False

    def __init__(self, selectable, name):
        self.selectable = selectable
        self.name = name


@compiles(CreateTemporaryTable)
def _create_temporary_table(element, compiler, **_):
    selectable = compiler.sql_compiler.process(
        element.selectable, literal_binds=True)
    return f'CREATE TEMPORARY TABLE {element.name} AS {selectable}'


class temporary_table(TableClause):

    inherit_cache = False

    def __init__(self, selectable, name=None):
        if name is None:
            name = 'temp_' + str(uuid4()).replace('-', '_')
        super().__init__(name)
        self._selectable = selectable
        self._columns._populate_separate_keys(
            col._make_proxy(self) for col in selectable.selected_columns)

    def create(self, bind):
        return bind.execute(CreateTemporaryTable(self._selectable, self.name))
