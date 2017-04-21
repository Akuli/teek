import collections.abc
import functools
import itertools
import sys
import _tkinter


tk = None
counts = collections.defaultdict(itertools.count)
_callback_cache = {}     # {function: name}, see register_callback()


def init():
    # this stuff isn't thread-safe, but it doesn't need to be
    global tk
    if tk is not None:
        raise RuntimeError("call quit() before calling init() again")

    tk = _tkinter.create(None, sys.argv[0], 'Tk', 1, 1, 1, 0, None)
    tk.call('wm', 'withdraw', '.')     # try to abstract it away


def requires_init(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if tk is None:
            raise RuntimeError("%s.init() wasn't called" % __name__)
        return function(*args, **kwargs)
    return wrapper


@requires_init
def mainloop():
    tk.mainloop(0)


def quit():
    global tk
    if tk is not None:
        counts.clear()
        _callback_cache.clear()
        tk.call('destroy', '.')
        tk = None


def register_callback(func):
    try:
        if func in _callback_cache:
            return _callback_cache[func]
    except TypeError:
        # it's not hashable, so we need to register a new function every
        # time :(
        pass

    name = 'tkinder_callback_%d' % next(counts['callbacks'])
    tk.createcommand(name, func)
    return name
