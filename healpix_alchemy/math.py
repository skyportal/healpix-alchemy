"""Define SQLAlchemy bindings for trigonometric functions."""
from sqlalchemy.sql.functions import GenericFunction, ReturnTypeFromArgs
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.ext.compiler import compiles

__all__ = ['pi']
mod_dict = globals()


class pi(GenericFunction):
    type = Float


def _compile_trigd_default(trig):
    def compilefunc(element, compiler, **kw):
        arg, = element.clauses
        return compiler.process(trig(arg * pi() / 180.0), **kw)
    return compilefunc


def _compile_trigd_postgresql(element, compiler, **kw):
    return compiler.visit_function(element)


for name in ['cos', 'sin', 'tan']:
    mod_dict[name] = type(name, (ReturnTypeFromArgs,), {})
    __all__.append(name)
    named = f'{name}d'
    mod_dict[named] = type(named, (ReturnTypeFromArgs,), {})
    compiles(mod_dict[named])(_compile_trigd_default(mod_dict[name]))
    compiles(mod_dict[named], 'postgresql')(_compile_trigd_postgresql)

del mod_dict, GenericFunction, ReturnTypeFromArgs, \
    _compile_trigd_default, _compile_trigd_postgresql
__all__ = tuple(__all__)
