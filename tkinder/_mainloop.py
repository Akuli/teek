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
        _app = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)
        _app.call('wm', 'withdraw', '.')


def _to_tcl(value):
    try:
        # duck-typing ftw (especially when avoiding circular imports)
        return value.widget_path
    except AttributeError:
        # it's not a widget
        pass

    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, collections.abc.Mapping):
        return tuple(map(_to_tcl, _flatten(value.items())))
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, numbers.Real):    # after bool check, bools are ints
        return str(value)

    # assume it's some kind of iterable, this must be after the Mapping
    # and str stuff above
    return tuple(map(_to_tcl, value))


def _pairs(sequence):
    assert len(sequence) % 2 == 0, "cannot divide %r into pairs" % (sequence,)
    return zip(sequence[0::2], sequence[1::2])


def _from_tcl(type_spec, value):
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

    if type_spec in (int, float):
        return type_spec(str(value))

    if type_spec is bool:
        try:
            return _app.getboolean(value)
        except _tkinter.TclError as e:
            raise ValueError(str(e)).with_traceback(e.__traceback__) from None

    # duck typing is great, especially when avoiding circular imports
    if isinstance(type_spec, type) and hasattr(type_spec, 'from_widget_path'):
        # class with a from_widget_path() method, probably Widget or a
        # subclass of it
        return type_spec.from_widget_path(str(value))

    if isinstance(type_spec, list):
        # [int] -> [1, 2, 3]
        (item_spec,) = type_spec
        return [_from_tcl(item_spec, item) for item in _app.splitlist(value)]

    if isinstance(type_spec, tuple):
        # (int, str) -> (1, 'hello')
        items = _app.splitlist(value)
        if len(type_spec) != len(items):
            raise ValueError("expected a sequence of %d items, got %r"
                             % (len(type_spec), list(items)))
        return tuple(map(_from_tcl, type_spec, items))

    if isinstance(type_spec, dict):
        # {str, [int]} -> {'a': [1, 2], 'b': [3, 4]}
        # TODO: support type_specs like {'a': int, 'b': str}
        [(key_spec, value_spec)] = type_spec.items()
        return {
            _from_tcl(key_spec, key): _from_tcl(value_spec, value)
            for key, value in _pairs(_app.splitlist(value))
        }

    if type_spec == 'color':
        return get_color(value)

    raise ValueError("unknown type specification " + repr(type_spec))


def call(returntype, command, *arguments):
    """Execute a Tcl command and return its return value.

    Everything is a string in Tcl but many things aren't in Python, so
    all arguments are converted to strings and the return value is
    converted to whatever is specified with *returntype*.

    Arguments are converted like this:

        * If the argument is a string, no conversions are done.
        * None is turned into an empty string.
        * :class:`Mappings <collections.abc.Mapping>` are turned into
          lists of pairs like those returned by :man:`dict(3tcl)`.
        * True and False are converted to ``1`` and ``0``.
        * :class:`Numbers <numbers.Number>` are passed to ``str``.
        * Iterables are treated as Tcl lists.
        * Any other arguments raise :exc:`TypeError`. Currently the
          error comes from attempting to iterate over the argument (and
          that's an implementation detail), but :exc:`TypeError` is
          guaranteed to be raised when an unknown argument is passed.

    The *returntype* can have values like this:

    ``None``
        The Tcl return value is ignored, and ``call()`` returns None.

    ``str``
        Usually no conversions are done. If Tcl uses an non-string
        representation of the object for performance reasons it will be
        forced to a string.

    ``int``, ``float``
        These are self-explanatory. :exc:`ValueError` may be raised.

    ``bool``
        This returns a Python boolean. All valid Tcl booleans are
        supported; for example, ``Y``, ``yes``, ``1``, ``on`` and
        ``tru`` are all converted to ``True``. :exc:`ValueError` is
        raised if the value is not a valid Tcl boolean.

    the string ``'color'``
        This is equivalent to using ``str`` with :func:`get_color`. Thus
        it converts everything to ``'#rrggbb'`` and raises ValueError.

    These examples use ``str`` and ``int``, but all other forms work as
    well:

    ``[str]``
        List of strings. Can be of any length.

    ``(str, int)``
        A tuple of a string and an integer. This allows you to create a
        sequence with different kinds of items in it. For example,
        ``(str, str, str)`` is like ``[str]`` except that it also checks
        the length of the result (raising :exc:`ValueError`) and returns
        a tuple instead of a list.

    ``{str: int}``
        Dictionary with string keys and integer values. Tcl dicts are
        just lists that contains an even number of items, so something
        like ``{str: str}`` is equivalent to using ``[str]`` and then
        making a list from that.

    You can nest things however you like. For example, ``[[int]]`` is a
    two-dimensional list of integers.

    Examples::

        >>> call([str], 'list', 'a', 'b', 'c')
        ['a', 'b', 'c']
        >>> call((str, int, float), 'list', 'hello', '3', '3.14')
        ('hello', 3, 3.14)
        >>> call([bool], 'list', 'yes', 'ye', 'true', 't', 'on', '1')
        [True, True, True, True, True, True]
        >>> call({str: [int]}, 'dict', 'create', 'a', '1', 'b', '2')   \
        # doctest: +SKIP
        {'a': [1], 'b': [2]}
        >>> call([str], 'list', 123, 3.14, None, 'hello')
        ['123', '3.14', '', 'hello']
    """
    _maybe_init()
    result = _app.call(tuple(map(_to_tcl, (command,) + arguments)))
    return _from_tcl(returntype, result)


def eval(returntype, string):
    """Like :func:`call`, but evaluates a string.

    >>> eval(None, 'proc add {a b} { return [expr $a + $b] }')
    >>> eval(int, 'add 1 2')
    3
    >>> call(int, 'add', 1, 2)      # usually this is better
    3
    """
    _maybe_init()
    result = _app.eval(string)
    return _from_tcl(returntype, result)


def get_color(string):
    """Convert any Tk-compatible color to a hexadecimal ``'#rrggbb'`` string.

    The returned color string is always lowercase.

    >>> get_color('red')
    '#ff0000'
    >>> get_color('#f00')
    '#ff0000'
    >>> get_color('#FFFF00000000')
    '#ff0000'
    """
    try:
        rgb = call([int], 'winfo', 'rgb', '.', string)
    except _tkinter.TclError as e:
        if str(e).startswith('unknown color name'):
            raise ValueError(str(e)) from None
        raise e     # pragma: no cover

    # tk uses 16-bit colors, but most people are more familiar with
    # 8-bit colors so we'll shift away the useless bits
    r, g, b = (value >> 8 for value in rgb)
    return '#%02x%02x%02x' % (r, g, b)


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
            return _to_tcl(func(*args, **kwargs))
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
