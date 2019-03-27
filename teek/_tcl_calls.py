import collections
import functools
import itertools
import numbers
import queue
import sys
import threading
import traceback
import _tkinter

import teek

_flatten = itertools.chain.from_iterable


# "converting errors" means raising teek's TclError when _tkinter raises
# its TclError
def _raise_converted_error(tkinter_error):
    raise (teek.TclError(str(tkinter_error))
           .with_traceback(tkinter_error.__traceback__)) from None


def _convert_errors(func):
    @functools.wraps(func)
    def result(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except _tkinter.TclError as e:
            _raise_converted_error(e)

    return result


counts = collections.defaultdict(lambda: itertools.count(1))


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


class _TclInterpreter:

    @_convert_errors
    def __init__(self):
        assert threading.current_thread() is threading.main_thread()
        # get_ident() is faster than threading.current_thread(), so that is
        # used elsewhere in the performance-critical stuff
        self._main_thread_ident = threading.get_ident()

        self._init_threads_called = False

        # tkinter does this :D i have no idea what each argument means
        self._app = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)

        self._app.call('wm', 'withdraw', '.')
        self._app.call('package', 'require', 'Ttk')

        # when a main-thread-needing function is called from another thread, a
        # tuple like this is added to this queue:
        #
        #    (func, args, kwargs, future)
        #
        # func is a function that MUST be called from main thread
        # args and kwargs are arguments for func
        # future will be set when the function has been called
        #
        # the function is called from Tk's event loop
        self._call_queue = queue.Queue()

    @_convert_errors
    def init_threads(self, poll_interval_ms=50):
        if threading.get_ident() != self._main_thread_ident:
            raise RuntimeError(
                "init_threads() must be called from main thread")

        # there is a race condition here, but if it actually creates problems,
        # you are doing something very wrong
        if self._init_threads_called:
            raise RuntimeError("init_threads() was called twice")

        # hard-coded name is ok because there is only one of these in each
        # Tcl interpreter
        poller_tcl_command = 'teek_init_threads_queue_poller'

        after_id = None

        @_convert_errors
        def poller():
            nonlocal after_id

            while True:
                try:
                    item = self._call_queue.get(block=False)
                except queue.Empty:
                    break

                func, args, kwargs, future = item
                try:
                    value = func(*args, **kwargs)
                except Exception as e:
                    future.set_error(e)
                else:
                    future.set_value(value)

            after_id = self._app.call(
                'after', poll_interval_ms, 'teek_init_threads_queue_poller')

        self._app.createcommand(poller_tcl_command, poller)

        def quit_disconnecter():
            if after_id is not None:
                self._app.call('after', 'cancel', after_id)

        teek.before_quit.connect(quit_disconnecter)

        poller()
        self._init_threads_called = True

    # no, don't do kwargs=None and then check for Noneness and kwargs={} etc
    # that made my test code run about 5% slower, because this is called a lot
    def call_thread_safely(self, non_threadsafe_func, args=(), kwargs={}, *,
                           convert_errors=True):
        try:
            if threading.get_ident() == self._main_thread_ident:
                return non_threadsafe_func(*args, **kwargs)

            if not self._init_threads_called:
                raise RuntimeError("init_threads() wasn't called")

            future = _Future()
            self._call_queue.put((non_threadsafe_func, args, kwargs, future))
            return future.get_value()
        except _tkinter.TclError as e:
            if convert_errors:
                _raise_converted_error(e)
            raise e

    # self._app must be accessed from the main thread, and this class provides
    # methods for calling it thread-safely

    @_convert_errors
    def run(self):
        if threading.get_ident() != self._main_thread_ident:
            raise RuntimeError("run() must be called from main thread")

        # no idea what the 0 does, tkinter calls it like this
        self._app.mainloop(0)

    def getboolean(self, arg):
        return self.call_thread_safely(self._app.getboolean, [arg])

    # _tkinter returns tuples when tcl represents something as a
    # list internally, but this forces it to string
    def get_string(self, from_underscore_tkinter):
        if isinstance(from_underscore_tkinter, str):
            return from_underscore_tkinter
        if isinstance(from_underscore_tkinter, _tkinter.Tcl_Obj):
            return from_underscore_tkinter.string

        # it's probably a tuple, i think because _tkinter returns tuples when
        # tcl represents something as a list internally, this forces tcl to
        # represent it as a string instead
        result = self.call_thread_safely(
            self._app.call, ['format', '%s', from_underscore_tkinter])
        assert isinstance(result, str)
        return result

    def splitlist(self, value):
        return self.call_thread_safely(self._app.splitlist, [value])

    def call(self, *args):
        return self.call_thread_safely(self._app.call, args)

    def eval(self, code):
        return self.call_thread_safely(self._app.eval, [code])

    def createcommand(self, name, func):
        return self.call_thread_safely(self._app.createcommand, [name, func])

    def deletecommand(self, name):
        return self.call_thread_safely(self._app.deletecommand, [name])


# a global _TclInterpreter instance
_interp = None


# these are the only functions that access _interp directly
def _get_interp():
    global _interp

    if _interp is None:
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("init_threads() wasn't called")
        _interp = _TclInterpreter()
    return _interp


def quit():
    """Stop the event loop and destroy all widgets.

    This function calls ``destroy .`` in Tcl, and that's documented in
    :man:`destroy(3tk)`. Note that this function does not tell Python to quit;
    only teek quits, so you can do this::

        import teek

        window = teek.Window()
        teek.Button(window, "Quit", teek.quit).pack()
        teek.run()
        print("Still alive")

    If you click the button, it interrupts ``teek.run()`` and the print runs.
    """
    global _interp

    if threading.current_thread() is not threading.main_thread():
        # TODO: allow quitting from other threads or document this
        raise RuntimeError("can only quit from main thread")

    if _interp is not None:
        teek.before_quit.run()
        _interp.call('destroy', '.')

        # to avoid a weird errors, see test_weird_error in test_tcl_calls.py
        for command in teek.tcl_call([str], 'info', 'commands'):
            if command.startswith('teek_command_'):
                delete_command(command)

        _interp = None
        teek.after_quit.run()


def run():
    """Runs the event loop until :func:`~teek.quit` is called."""
    _get_interp().run()


def init_threads(poll_interval_ms=50):
    """Allow using teek from other threads than the main thread.

    This is implemented with a queue. This function starts an
    :ref:`after callback <after-cb>` that checks for new messages in the queue
    every 50 milliseconds (that is, 20 times per second), and when another
    thread calls a teek function that does a :ref:`Tcl call <tcl-calls>`,
    the information required for making the Tcl call is put to the queue and
    the Tcl call is done by the after callback.

    .. note::
        After callbacks don't work without the event loop, so make sure to run
        the event loop with :func:`.run` after calling :func:`.init_threads`.

    ``poll_interval_ms`` can be given to specify a different interval than 50
    milliseconds.

    When a Tcl call is done from another thread, that thread blocks until the
    after callback has handled it, which is slow. If this is a problem, there
    are two things you can do:

    * Use a smaller ``poll_interval_ms``. Watch your CPU usage though; if you
      make ``poll_interval_ms`` too small, you might get 100% CPU usage when
      your program is doing nothing.
    * Try to rewrite the program so that it does less teek stuff in threads.
    """
    _get_interp().init_threads()


def make_thread_safe(func):
    """A decorator that makes a function safe to be called from any thread.

    Functions decorated with this always run in the event loop, and therefore
    in the main thread.

    Most of the time you don't need to use this yourself; teek uses this a
    lot internally, so most teek things are already thread safe. However, if
    you have code like this...
    ::

        def bad_func123():
            func1()
            func2()
            func3()

    ...where ``func1``, ``func2`` and ``func3`` do teek things and you need
    to call ``func123`` from a thread, it's best to decorate ``func123``::

        @teek.make_thread_safe
        def good_func123():
            func1()
            func2()
            func3()

    This may make ``func123`` noticably faster. If a function decorated with
    ``make_thread_safe()`` is called from some other thread than the main
    thread, it needs to communicate between the main thread and teek's event
    loop, which is slow. However, with ``good_func123``, there isn't much
    communication to do: the other thread needs to tell the main thread to run
    the function, and later the main thread tells the other thread that the
    function has finished running. The ``bad_func123`` function does this 3
    times, once in each line of code.

    .. note::
        Functions decorated with ``make_thread_safe()`` must not block because
        they are ran in the event loop. In other words, this code is bad,
        because it will freeze the GUI for about 5 seconds::

            @teek.make_thread_safe
            def do_stuff():
                time.sleep(5)
    """
    @functools.wraps(func)
    def safe(*args, **kwargs):
        return _get_interp().call_thread_safely(func, args, kwargs,
                                                convert_errors=False)

    return safe


def to_tcl(value):
    # these are ordered so that performance is good
    # please profile when changing order
    if isinstance(value, str):
        return value
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else '0'

    try:
        to_tcl_method = value.to_tcl
    except AttributeError:
        pass
    else:
        return to_tcl_method()

    if isinstance(value, numbers.Real):    # after bool check, bools are ints
        return str(value)
    if isinstance(value, collections.abc.Mapping):
        return tuple(map(to_tcl, _flatten(value.items())))

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
        return _get_interp().get_string(value)

    if type_spec is bool:
        if not from_tcl(str, value):
            # '' is not a valid bool, but this is usually what was intended
            return None

        try:
            return _get_interp().getboolean(value)
        except teek.TclError as e:
            raise ValueError(str(e)).with_traceback(e.__traceback__) from None

    # special case to allow bases other than 10 and empty strings
    if type_spec is int:
        stringed_value = from_tcl(str, value)
        if not stringed_value:
            return None
        return int(stringed_value, 0)

    if isinstance(type_spec, type):     # it's a class
        if issubclass(type_spec, numbers.Real):     # must be after bool check
            string = from_tcl(str, value)
            if not string:
                return None
            return type_spec(string)

        if hasattr(type_spec, 'from_tcl'):
            string = from_tcl(str, value)

            # the empty string is the None value in tcl
            if not string:
                return None

            return type_spec.from_tcl(string)

    elif isinstance(type_spec, (list, tuple, dict)):
        items = _get_interp().splitlist(from_tcl(str, value))

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
            # {'a': int, 'b': str} -> {'a': 1, 'b': 'lol', 'c': 'str assumed'}
            result = {}
            for key, value in _pairs(items):
                key = from_tcl(str, key)
                result[key] = from_tcl(type_spec.get(key, str), value)
            return result

        raise RuntimeError("this should never happen")      # pragma: no cover

    raise TypeError("unknown type specification " + repr(type_spec))


def tcl_call(returntype, command, *arguments):
    """Call a Tcl command.

    The arguments are passed correctly, even if they contain spaces:

    >>> teek.tcl_eval(None, 'puts "hello world thing"')  # 1 arguments to puts\
        # doctest: +SKIP
    hello world thing
    >>> message = 'hello world thing'
    >>> teek.tcl_eval(None, 'puts %s' % message)  # 3 args to puts, tcl error
    Traceback (most recent call last):
        ...
    teek.TclError: wrong # args: should be "puts ?-nonewline? ?channelId? \
string"
    >>> teek.tcl_call(None, 'puts', message)   # 1 arg to puts\
        # doctest: +SKIP
    hello world thing
    """
    result = _get_interp().call(tuple(map(to_tcl, (command,) + arguments)))
    return from_tcl(returntype, result)


def tcl_eval(returntype, code):
    """Run a string of Tcl code.

    >>> teek.tcl_eval(None, 'proc add {a b} { return [expr $a + $b] }')
    >>> teek.tcl_eval(int, 'add 1 2')
    3
    >>> teek.tcl_call(int, 'add', 1, 2)     # usually this is better, see below
    3
    """
    result = _get_interp().eval(code)
    return from_tcl(returntype, result)


# because there's no better place for this
def update(*, idletasks_only=False):
    """Handles all pending events, and returns when they are all handled.

    See :man:`update(3tcl)` for details. If ``idletasks_only=True`` is given,
    this calls ``update idletasks``; otherwise, this calls ``update`` with no
    arguments.
    """
    if idletasks_only:
        tcl_call(None, 'update', 'idletasks')
    else:
        tcl_call(None, 'update')


# TODO: maybe some magic that uses type hints for this?
@make_thread_safe
def create_command(func, arg_type_specs=(), *, extra_args_type=None):
    """Create a Tcl command that calls ``func``.

    Here is a simple example:

    >>> tcl_print = teek.create_command(print, [str])  # calls print(a_string)
    >>> tcl_print       # doctest: +SKIP
    'teek_command_1'
    >>> teek.tcl_call(None, tcl_print, 'hello world')
    hello world
    >>> teek.tcl_eval(None, '%s "hello world"' % tcl_print)
    hello world

    Created commands should be deleted with :func:`.delete_command` when they
    are no longer needed.

    The function will take ``len(arg_type_specs)`` arguments, and the arguments
    are converted to Python objects using ``arg_type_specs``. The
    ``arg_type_specs`` must be a sequence of
    :ref:`type specifications <type-spec>`.

    If ``extra_args_type`` is given, the function can also take more than
    ``len(arg_type_specs)`` arguments, and the type of each extra argument will
    be *extra_args_type*. For example:

    >>> def func(a, b, *args):
    ...     print(a - b)
    ...     for arg in args:
    ...         print(arg)
    ...
    >>> command = teek.create_command(func, [int, int], extra_args_type=str)
    >>> teek.tcl_call(None, command, 123, 23, 'asd', 'toot', 'boom boom')
    100
    asd
    toot
    boom boom

    The return value from the Python function is
    :ref:`converted to a string for Tcl <to-tcl>`.

    If the function raises an exception, a traceback will be printed. However,
    the Tcl command returns an empty string on errors and does *not* raise an
    error in Tcl. Be sure to return a non-empty value on success if you want to
    do error handling in Tcl code.
    """
    # verbose is better than implicit
    stack_info = ''.join(traceback.format_stack())

    def real_func(*args):
        try:
            # python raises TypeError for wrong number of args
            if extra_args_type is None:
                expected = "%d arguments" % len(arg_type_specs)
                ok = (len(args) == len(arg_type_specs))
            else:
                expected = "at least %d arguments" % len(arg_type_specs)
                ok = (len(args) >= len(arg_type_specs))
            if not ok:
                raise TypeError("expected %s, got %d arguments"
                                % (expected, len(args)))

            # map(func, a, b) stops when the shortest of a and b ends
            basic_args = map(from_tcl,
                             arg_type_specs, args[:len(arg_type_specs)])
            extra_args = (from_tcl(extra_args_type, arg)
                          for arg in args[len(arg_type_specs):])

            # func(*basic_args, *extra_args) doesn't work in 3.4
            # basic_args + extra_args doesn't work because they are iterators
            return to_tcl(func(*itertools.chain(basic_args, extra_args)))

        except Exception:
            traceback_blabla, rest = traceback.format_exc().split('\n', 1)
            print(traceback_blabla + '\n' + stack_info + rest,
                  end='', file=sys.stderr)
            return ''

    name = 'teek_command_%d' % next(counts['commands'])
    _get_interp().createcommand(name, real_func)
    return name


@make_thread_safe
def delete_command(name):
    """Delete a Tcl command by name.

    You can delete commands returned from :func:`create_command` to
    avoid memory leaks.
    """
    _get_interp().deletecommand(name)
