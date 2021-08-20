import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import DDLElement


@pytest.fixture(params=['postgresql', 'sqlite'])
def engine(request):
    """Create an SQLAlchemy engine with a disposable PostgreSQL database."""
    if request.param == 'postgresql':
        postgresql = request.getfixturevalue('postgresql')
        return create_engine('postgresql://',
                             poolclass=StaticPool,
                             creator=lambda: postgresql)
    else:  # sqlite
        return create_engine('sqlite://', poolclass=StaticPool)


@pytest.fixture
def session(engine, record_database_size):
    """Create an SQLAlchemy session with a disposable PostgreSQL database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    record_database_size()
    session.close()


class GetDatabaseSize(DDLElement):
    pass


@compiles(GetDatabaseSize, 'postgresql')
def visit_get_database_size_postgresql(element, compiler, **kwargs):
    return '''SELECT sum(pg_relation_size(C.oid))
              FROM pg_class C
              LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
              WHERE nspname NOT IN ('pg_catalog', 'information_schema')'''


@compiles(GetDatabaseSize, 'sqlite')
def visit_get_database_size_sqlite(element, compiler, **kwargs):
    return '''SELECT page_count * page_size
              FROM pragma_page_count, pragma_page_size'''


@pytest.fixture
def record_database_size(record_property, engine):

    def func():
        (database_size,), = engine.execute(GetDatabaseSize())
        record_property('database_size', database_size)

    return func


def pytest_terminal_summary(terminalreporter):
    terminalreporter.section('database size')
    for report in terminalreporter.getreports(''):
        try:
            database_size = dict(report.user_properties)['database_size']
        except KeyError:
            pass
        else:
            terminalreporter.line(f'{report.nodeid}: {database_size}')
