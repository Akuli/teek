import sys
import traceback


class Callback:
    """An object that calls multiple functions.

    Example::

        >>> c = Callback()
        >>> c.connect(print, args=["hello", "world"])
        >>> c.connect(print, args=["hello", "again"])
        >>> c.run()      # usually tkinder does this
        hello world
        hello again
    """

    def __init__(self, *types):
        self._argtypes = types
        self._connections = []

    def connect(self, function, args=(), kwargs=None):
        """Schedule ``callback(*args, **kwargs)`` to run.

        If the callback has its own arguments (e.g.
        ``Callback(int, int)``), they will appear before the *args*
        given here. For example::

            >>> c = Callback(int, int)
            >>> c.connect(print, args=['hello'], kwargs={'sep': '-'})
            >>> c.run(1, 2)
            1-2-hello
        """
        # -1 is this method so -2 is what called this
        stack_info = traceback.format_stack()[-2]

        if kwargs is None:
            kwargs = {}
        self._connections.append((function, args, kwargs, stack_info))

    def disconnect(self, function):
        """Undo a :meth:`~connect` call.

        Note that this method doesn't do anything to the *args* and
        *kwargs* passed to :meth:`~connect`, so when disconnecting a
        function connected multiple times with different arguments, only
        the first connection is undone.

        >>> c = Callback()
        >>> c.connect(print, ["hello"])
        >>> c.connect(print, ["hello", "again"])
        >>> c.run()
        hello
        hello again
        >>> c.disconnect(print)
        >>> c.run()
        hello
        """
        # enumerate objects aren't reversible :(
        for index in range(len(self._connections)-1, -1, -1):
            # can't use is because cpython does this:
            #   >>> class Thing:
            #   ...   def stuff(): pass
            #   ...
            #   >>> t = Thing()
            #   >>> t.stuff == t.stuff
            #   True
            #   >>> t.stuff is t.stuff
            #   False
            if self._connections[index][0] == function:
                del self._connections[index]
                return

        raise ValueError("not connected: %r" % (function,))

    def run(self, *args):
        """Run the connected callbacks."""
        if (len(args) != len(self._argtypes) or
                not all(map(isinstance, args, self._argtypes))):
            good = ', '.join(cls.__name__ for cls in self._argtypes)
            bad = ', '.join(type(arg).__name__ for arg in args)
            raise TypeError("should be run(%s), not run(%s)" % (good, bad))

        for func, extra_args, kwargs, stack_info in self._connections:
            try:
                func(*(args + tuple(extra_args)), **kwargs)
            except Exception:
                traceback_blabla, rest = traceback.format_exc().split('\n', 1)
                print(traceback_blabla, file=sys.stderr)
                print(stack_info + rest, end='', file=sys.stderr)
                break
