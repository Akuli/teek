import collections
import functools
import itertools
import numbers
import queue
import sys
import threading
import traceback
import _tkinter

from pythotk import _structures

_flatten = itertools.chain.from_iterable


on_quit = _structures.Callback()

counts = collections.defaultdict(lambda: itertools.count(1))
on_quit.connect(counts.clear)


# because readability is good
# TODO: is there something like this in e.g. concurrent.futures?
class _Future:

    def __init__(self):
        self._value = None
        self._error = None
        self._event = threading.Event()
        self._success = None

    def set_value(self, value):
        self._value = value
        self._success = True
        self._event.set()

    def set_error(self, exc):
        self._error = exc
        self._success = False
        self._event.set()

    def get_value(self):
        self._event.wait()
        assert self._success is not None
        if not self._success:
            raise self._error
        return self._value


# when call or eval is called from some other thread than the main thread, a
# tuple like this is added to this queue:
#
#    (func, args, kwargs, future)
#
# * func is a function that MUST be called from main thread
# * args and kwargs are arguments for func
# * future will be set when the function has been called from Tk's event loop
_main_thread_call_queue = queue.Queue()

# globalz ftw
# TODO: use less globals, this is kind of creepy
_app = None

_init_threads_called = False
on_quit.connect(lambda: globals().update({'_init_threads_called': False}))


# this must be called from main thread
def _get_app():
    global _app

    assert threading.current_thread() is threading.main_thread()
    if _app is None:
        # tkinter does this :D i have no idea what each argument means
        _app = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)

        _app.call('wm', 'withdraw', '.')
        _app.call('package', 'require', 'tile')

    return _app


def init_threads(poll_interval_ms=50):
    global _init_threads_called

    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("init_threads() must be called from main thread")

    # there is a race condition here, but if it actually creates problems, you
    # are doing something very wrong
    if _init_threads_called:
        raise RuntimeError("init_threads() was called twice")

    unique_number = str(next(counts['init_threads_poller']))
    poller_tcl_command = 'pythotk_init_threads_queue_poller_' + unique_number

    after_id = None

    def poller():
        nonlocal after_id

        while True:
            try:
                item = _main_thread_call_queue.get(block=False)
            except queue.Empty:
                break

            func, args, kwargs, future = item
            try:
                value = func(*args, **kwargs)
            except Exception as e:
                future.set_error(e)
            else:
                future.set_value(value)

        after_id = _get_app().call(
            'after', poll_interval_ms, poller_tcl_command)

    _get_app().createcommand(poller_tcl_command, poller)
    on_quit.connect(
        lambda: None if after_id is None else _get_app().call(
            'after', 'cancel', after_id))

    poller()
    _init_threads_called = True


def _call_thread_safely(non_threadsafe_func, args=(), kwargs=None):
    if kwargs is None:
        kwargs = {}

    if threading.current_thread() is threading.main_thread():
        return non_threadsafe_func(*args, **kwargs)

    if not _init_threads_called:
        raise RuntimeError("init_threads() wasn't called")

    future = _Future()
    _main_thread_call_queue.put((non_threadsafe_func, args, kwargs, future))
    return future.get_value()


def _thread_safe(func):
    @functools.wraps(func)
    def safe(*args, **kwargs):
        return _call_thread_safely(func, args, kwargs)

    return safe


@_thread_safe
def quit():
    global _app
    if _app is not None:
        on_quit.run()
        _app.call('destroy', '.')
        _app = None


def run():
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("run() must be called from main thread")

    # no idea what the 0 does, tkinter calls it like this
    _get_app().mainloop(0)


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
            # force it to string, this doesn't recurse if concat returns
            # a string, which it seems to always do
            concatted = _call_thread_safely(
                lambda: _get_app().call('concat', 'junk', value))
            junk, result = concatted.split(maxsplit=1)
            assert junk == 'junk'
            return result
        return str(value)

    if type_spec is bool:
        if not from_tcl(str, value):
            # '' is not a valid bool, but this is usually what was intended
            # TODO: document this
            return None

        try:
            return _call_thread_safely(lambda: _get_app().getboolean(value))
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

    elif isinstance(type_spec, (list, tuple, dict)):
        items = _call_thread_safely(lambda: _get_app().splitlist(value))

        if isinstance(type_spec, list):
            # [int] -> [1, 2, 3]
            (item_spec,) = type_spec
            return [from_tcl(item_spec, item) for item in items]

        if isinstance(type_spec, tuple):
            # (int, str) -> (1, 'hello')
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
                for key, value in _pairs(items)
            }

        raise RuntimeError("this should never happen")      # pragma: no cover

    raise TypeError("unknown type specification " + repr(type_spec))


@_thread_safe
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
    result = _get_app().call(tuple(map(to_tcl, (command,) + arguments)))
    return from_tcl(returntype, result)


@_thread_safe
def eval(returntype, code):
    """Run a string of Tcl code.

    >>> eval(None, 'proc add {a b} { return [expr $a + $b] }')
    >>> eval(int, 'add 1 2')
    3
    >>> call(int, 'add', 1, 2)      # usually this is better, see below
    3
    """
    result = _get_app().eval(code)
    return from_tcl(returntype, result)


_command_cache = {}     # {function: name}
on_quit.connect(_command_cache.clear)


# TODO: add support for passing arguments!
@_thread_safe
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

    name = 'pythotk_command_%d' % next(counts['commands'])
    _get_app().createcommand(name, real_func)
    if cache_key is not None:
        _command_cache[cache_key] = name
    return name


@_thread_safe
def delete_command(name):
    """Delete a Tcl command by name.

    You can delete commands returned from :func:`create_command` to
    avoid memory leaks.
    """
    _get_app().deletecommand(name)
