import inspect
import typing

from sqlalchemy.ext.declarative import declared_attr


class InheritTableArgs:
    """Inherit SQLAlchemy ``__table_args__`` from a parent class.

    Defining SQLAlchemy model derived classes and correctly inheriting the
    ``__table_args__`` from the parent class is tricky because
    ``__table_args__`` can be either a dictionary of keyword arguments or a
    tuple of position arguments and a terminal element that is a dictionary of
    keyword arguments.

    This helper function aids in correctly overriding and inheriting
    ``__table_args__``.

    Usage
    -----
    ::

        class Foo(InheritTableArgs, Bar):

            @declared_attr
            def __table_args__(cls):
                *args, kwargs = super_table_args(cls)
                args = (*args, 'bar', 'bat')  # Add more position args
                kwargs = {**kwargs, 'baz': 3}  # Add more kwargs
                return *args, kwargs

    """
    @declared_attr
    def __table_args__(cls):
        try:
            table_args = super().__table_args__
        except AttributeError:
            table_args = ()

        if isinstance(table_args, typing.Mapping):
            return table_args,
        elif not isinstance(table_args, typing.Sequence):
            raise ValueError('table_args must be a mapping or sequence')
        elif not table_args or not isinstance(table_args[-1], typing.Mapping):
            return (*table_args, {})
        else:
            return table_args


def default_and_onupdate(func):
    """Provide a function to generate default values for SQLAlchemy columns.

    Usage
    -----

    ::

        class Foo(Base):
            ra = Column(Float)
            dec = Column(BigInteger)
            x = Column(
                Float,
                **default_and_onupdate(
                    lambda ra, dec: math.cos(ra) * math.sin(dec)))

    """
    keys = inspect.getfullargspec(func).args

    def wrapper(context):
        params = context.get_current_parameters()
        return func(*(params[key] for key in keys))

    return dict.fromkeys(('default', 'onupdate'), wrapper)
