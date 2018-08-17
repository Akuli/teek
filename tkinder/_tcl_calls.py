import collections
import itertools
import numbers
import sys
import traceback
import _tkinter

from tkinder import _structures

_flatten = itertools.chain.from_iterable


on_quit = _structures.Callback()

counts = collections.defaultdict(lambda: itertools.count(1))
on_quit.connect(counts.clear)

_app = None


def _maybe_init():
    global _app
    if _app is None:
        # tkinter does this :D
        _app = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)

        _app.call('wm', 'withdraw', '.')
        _app.call('package', 'require', 'tile')


def to_tcl(value):
    if hasattr(value, 'to_tcl'):    # duck-typing ftw
        return value.to_tcl()

    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, collections.abc.Mapping):
        return tuple(map(to_tcl, _flatten(value.items())))
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, numbers.Real):    # after bool check, bools are ints
        return str(value)

    # assume it's some kind of iterable, this must be after the Mapping
    # and str stuff above
    return tuple(map(to_tcl, value))


def _pairs(sequence):
    assert len(sequence) % 2 == 0, "cannot divide %r into pairs" % (sequence,)
    return zip(sequence[0::2], sequence[1::2])


def from_tcl(type_spec, value):
    if type_spec is None:
        return None

    if type_spec is str:
        # _tkinter returns tuples when tcl represents something as a
        # list internally
        if isinstance(value, tuple):
            # force it to string
            junk, result = _app.call('concat', 'junk', value).split(maxsplit=1)
            assert junk == 'junk'
            return result
        return str(value)

    if type_spec is bool:
        if not from_tcl(str, value):
            # '' is not a valid bool, but this is usually what was intended
            # TODO: document this
            return None

        try:
            return _app.getboolean(value)
        except (_tkinter.TclError, ValueError) as e:
            raise ValueError(str(e)).with_traceback(e.__traceback__) from None

    if isinstance(type_spec, type):     # it's a class
        if issubclass(type_spec, numbers.Real):     # must be after bool check
            return type_spec(from_tcl(str, value))

        if hasattr(type_spec, 'from_tcl'):
            string = from_tcl(str, value)

            # the empty string is the None value in tcl
            if not string:
                return None

            return type_spec.from_tcl(string)

    else:
        if isinstance(type_spec, list):
            # [int] -> [1, 2, 3]
            (item_spec,) = type_spec
            return [from_tcl(item_spec, item) for item in _app.splitlist(value)]

        if isinstance(type_spec, tuple):
            # (int, str) -> (1, 'hello')
            items = _app.splitlist(value)
            if len(type_spec) != len(items):
                raise ValueError("expected a sequence of %d items, got %r"
                                 % (len(type_spec), list(items)))
            return tuple(map(from_tcl, type_spec, items))

        if isinstance(type_spec, dict):
            # {str, [int]} -> {'a': [1, 2], 'b': [3, 4]}
            # TODO: support type_specs like {'a': int, 'b': str}
            [(key_spec, value_spec)] = type_spec.items()
            return {
                from_tcl(key_spec, key): from_tcl(value_spec, value)
                for key, value in _pairs(_app.splitlist(value))
            }

    raise TypeError("unknown type specification " + repr(type_spec))


def check_type(type_spec, value):
    """Checks if a value matches a type specification.

    If the value doesn't match, this raises :exc:`ValueError` or
    :exc:`TypeError`.

    The objects that :func:`.call` and :func:`.eval` return should always
    match, so that after a call like
    ``result = tk.call(type_spec, something something)``,
    ``tk.check_type(type_spec, result)`` shouldn't raise errors.
    """
    if type_spec is None:   # accept anything
        return

    if isinstance(type_spec, type):     # it's a class
        if not isinstance(value, type_spec):
            raise TypeError("expected %s, got %r"
                            % (type_spec.__name__, value))
        return

    if isinstance(type_spec, (list, tuple)):
        # this raises TypeError if the value is not iterable
        if iter(value) is value:
            # value is an iterator, so can't loop over it to check anything
            # because that would exhaust it
            return

        if isinstance(type_spec, list):
            (item_spec,) = type_spec
            for item in value:
                check_type(item_spec, item)
        else:
            try:
                len(value)
            except TypeError:
                # the value is an iterable that doesn't have a len(), but it's
                # not an iterator so we don't need to worry about exhausting it
                pass
            else:
                if len(type_spec) != len(value):
                    raise ValueError("expected an iterable of %d items, got %r"
                                     % (len(type_spec), value))

            # if the value has no len(), the zip doesn't check whether its
            # iterator yields the same number of items as in type_spec, but
            # those cases are very rare anyway
            for item_spec, item in zip(type_spec, value):
                check_type(item_spec, item)

        return

    if isinstance(type_spec, dict):
        # anything with .items() is dicty enough because duck-typing
        [(key_spec, value_spec)] = type_spec.items()
        for key, value in value.items():
            check_type(key_spec, key)
            check_type(value_spec, value)
        return

    raise TypeError("unknown type specification " + repr(type_spec))


def call(returntype, command, *arguments):
    """Call a Tcl command.

    The arguments are passed correctly, even if they contain spaces:

    >>> tk.eval(None, 'puts "hello world thing"')  # 1 arguments to puts \
        # doctest: +SKIP
    hello world thing
    >>> message = 'hello world thing'
    >>> tk.eval(None, 'puts %s' % message)  # 3 arguments to puts, tcl error
    Traceback (most recent call last):
        ...
    _tkinter.TclError: wrong # args: should be "puts ?-nonewline? ?channelId? \
string"
    >>> tk.call(None, 'puts', message)   # 1 argument to puts  # doctest: +SKIP
    hello world thing
    """
    _maybe_init()
    result = _app.call(tuple(map(to_tcl, (command,) + arguments)))
    return from_tcl(returntype, result)


def eval(returntype, code):
    """Run a string of Tcl code.

    >>> eval(None, 'proc add {a b} { return [expr $a + $b] }')
    >>> eval(int, 'add 1 2')
    3
    >>> call(int, 'add', 1, 2)      # usually this is better, see below
    3
    """
    _maybe_init()
    result = _app.eval(code)
    return from_tcl(returntype, result)


def run():
    _maybe_init()
    _app.mainloop(0)


def quit():
    global _app
    if _app is not None:
        on_quit.run()
        _app.call('destroy', '.')
        _app = None


_command_cache = {}     # {function: name}
on_quit.connect(_command_cache.clear)


# TODO: add support for passing arguments!
def create_command(func, args=(), kwargs=None, stack_info=''):
    """Create a Tcl command that runs ``func(*args, **kwargs)``.

    The Tcl command's name is returned as a string. The return value is
    converted to string for Tcl similarly as with :func:`call`.

    If the function raises an exception, a traceback will be printed
    with *stack_info* right after the "Traceback (bla bla bla)" line.
    However, the Tcl command returns an empty string on errors and does
    *not* raise a Tcl error. Be sure to return a non-empty value on
    success if you want to do error handling in Tcl code.

    .. seealso::
        Use :func:`traceback.format_stack` to get a *stack_info* string.
    """
    _maybe_init()

    args = tuple(args)
    if kwargs is None:
        kwargs = {}
    cache_key = (func, args, tuple(kwargs.items()), stack_info)

    try:
        return _command_cache[cache_key]
    except KeyError:
        pass
    except TypeError:
        # something isn't hashable and we can't cache :( fortunately
        # this doesn't happen often
        cache_key = None

    def real_func():
        try:
            return to_tcl(func(*args, **kwargs))
        except Exception as e:
            traceback_blabla, rest = traceback.format_exc().split('\n', 1)
            print(traceback_blabla, file=sys.stderr)
            print(stack_info + rest, end='', file=sys.stderr)
            return ''

    name = 'tkinder_command_%d' % next(counts['commands'])
    _app.createcommand(name, real_func)
    if cache_key is not None:
        _command_cache[cache_key] = name
    return name


def delete_command(name):
    """Delete a Tcl command by name.

    You can delete commands returned from :func:`create_command` to
    avoid memory leaks.
    """
    _maybe_init()
    _app.deletecommand(name)
