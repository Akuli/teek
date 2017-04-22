import collections
import functools
import itertools
import sys
import traceback
import _tkinter

import tkinder
from tkinder import structures

on_quit = structures.Callback()

counts = collections.defaultdict(itertools.count)
on_quit.connect(counts.clear)


def init():
    # this stuff isn't thread-safe, but it doesn't need to be
    if tkinder.tk is not None:
        raise RuntimeError("call quit() before calling init() again")

    tkinder.tk = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)
    tkinder.tk.call('wm', 'withdraw', '.')     # try to abstract it away


def requires_init(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if tkinder.tk is None:
            raise RuntimeError("tkinder.init() wasn't called")
        return function(*args, **kwargs)
    return wrapper


@requires_init
def mainloop():
    tkinder.tk.mainloop(0)


def quit():
    if tkinder.tk is not None:
        on_quit.run()
        tkinder.tk.call('destroy', '.')
        tkinder.tk = None


_command_cache = {}     # {function: name}
on_quit.connect(_command_cache.clear)


def create_command(func, stack_info=None):
    """Create a Tcl command that runs ``func()`` and return its name.

    If the function raises an exception and *stack_info* is set, it will
    be printed in the beginning of the traceback. Use
    :func:`traceback.format_stack` to get a *stack_info* string.
    """
    try:
        return _command_cache[(func, stack_info)]
    except (KeyError, TypeError):
        # if we got a TypeError, func isn't hashable so we need to add a
        # new command every time :( fortunately it doesn't happen often
        pass

    def real_func():
        try:
            func()
        except Exception:
            if stack_info is None:
                traceback.print_exc()
            else:
                traceback_blabla, rest = traceback.format_exc().split('\n', 1)
                print(traceback_blabla, file=sys.stderr)
                print(stack_info + rest, end='', file=sys.stderr)

    name = 'tkinder_command_%d' % next(counts['commands'])
    tkinder.tk.createcommand(name, real_func)
    _command_cache[(func, stack_info)] = name
    return name
