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
            'select pg_size_pretty(pg_database_size(current_database()))')
        record_property('database_size', database_size)

    return func


def pytest_terminal_summary(terminalreporter):
    terminalreporter.section('Database size')
    for report in terminalreporter.getreports(''):
        try:
            database_size = dict(report.user_properties)['database_size']
        except KeyError:
            pass
        else:
            terminalreporter.line(f'{report.nodeid}: {database_size}')
