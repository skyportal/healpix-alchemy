import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def engine(postgresql):
    """Create an SQLAlchemy engine with a disposable PostgreSQL database."""
    return create_engine('postgresql://',
                         poolclass=StaticPool,
                         creator=lambda: postgresql)


@pytest.fixture
def session(engine, record_database_size):
    """Create an SQLAlchemy session with a disposable PostgreSQL database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    record_database_size()
    session.close()


@pytest.fixture
def record_database_size(record_property, engine):

    def func():
        (database_size,), = engine.execute(
            '''SELECT pg_size_pretty(sum(pg_relation_size(C.oid)))
               FROM pg_class C
               LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
               WHERE nspname NOT IN ('pg_catalog', 'information_schema')''')
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
