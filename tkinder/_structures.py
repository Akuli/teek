import sys
import traceback

import tkinder


class Callback:
    """An object that calls functions.

    Example::

        >>> c = Callback()
        >>> c.connect(print, args=["hello", "world"])
        >>> c.run()   # runs print("hello", "world"), usually tkinder does this
        hello world
        >>> c.connect(print, args=["hello", "again"])
        >>> c.run()
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
        given here. For example:

        >>> c = Callback(int, int)
        >>> c.connect(print, args=['hello'], kwargs={'sep': '-'})
        >>> c.run(1, 2)     # print(1, 2, 'hello', sep='-')
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
        for index in range(len(self._connections) - 1, -1, -1):
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


class Color:
    """Represents an RGB color.

    There are a few ways to create color objects:

    * ``Color(red, green, blue)`` creates a new color from an RGB value. The
      ``red``, ``green`` and ``blue`` should be integers between 0 and 255
      (inclusive).
    * ``Color(hex_string)`` creates a color from a hexadecimal color string.
      For example, ``Color('#ff0000')`` is equivalent to
      ``Color(0xff, 0x00, 0x00)`` where ``0xff`` is hexadecimal notation for
      255, and ``0x00`` is 0.
    * ``Color(color_name)`` creates a color object from a Tk color. There is a
      long list of color names in :man:`colors(3tk)`.

    Examples::

        >>> Color(255, 255, 255)    # r, g and b are all maximum, this is white
        <Color '#ffffff': red=255, green=255, blue=255>
        >>> Color('white')     # 'white' is a Tk color name
        <Color 'white': red=255, green=255, blue=255>

    The string argument things are implemented by letting Tk interpret the
    color, so all of the ways to define colors as strings shown in
    :man:`Tk_GetColor(3tk)` are supported.

    Color objects are hashable, and they can be compared with ``==``::

        >>> Color(0, 0, 255) == Color(0, 0, 255)
        True
        >>> Color(0, 255, 0) == Color(0, 0, 255)
        False

    Color objects are immutable. If you want to change a color, create a new
    Color object.

    .. attribute:: red
    .. attribute:: green
    .. attribute:: blue

        These are the values passed to ``Color()``.

        >>> Color(0, 0, 255).red
        0
        >>> Color(0, 0, 255).green
        0
        >>> Color(0, 0, 255).blue
        255

        Assigning to these like ``some_color.red = 255`` raises an exception.
    """

    def __init__(self, *args):
        if len(args) == 3:
            for name, value in zip(['red', 'green', 'blue'], args):
                if value not in range(256):
                    raise ValueError("invalid %s value: %r" % (name, value))
            self._color_string = '#%02x%02x%02x' % args
        elif len(args) == 1:
            self._color_string = args[0]
        else:
            # python raises TypeError for wrong number of arguments
            raise TypeError("use {0}(red, green, blue) or {0}(color_string)"
                            .format(type(self).__name__))

        # any widget will do, i'm using the '.' root window because it
        # always exists
        rgb = tkinder.call([int], 'winfo', 'rgb', '.', self._color_string)

        # tk uses 16-bit colors for some reason, but most people are more
        # familiar with 8-bit colors so we'll shift away the "useless" bits
        self._rgb = tuple(value >> 8 for value in rgb)
        assert len(self._rgb) == 3

    def __repr__(self):
        return '<%s %r: red=%d, green=%d, blue=%d>' % (
            type(self).__name__, self._color_string,
            self.red, self.green, self.blue)

    @classmethod
    def from_tcl(cls, color_string):
        """``Color.from_tcl(color_string)`` returns ``Color(color_string)``.

        This is just for compatibility with
        :ref:`type specifications <type-spec>`.
        """
        return cls(color_string)

    red = property(lambda self: self._rgb[0])
    green = property(lambda self: self._rgb[1])
    blue = property(lambda self: self._rgb[2])

    def to_tcl(self):
        """Return this color as a Tk-compatible string.

        The string is *often* a hexadecimal ``'#rrggbb'`` string, but not
        always; it can be also e.g. a color name like ``'white'``. Use
        :attr:`red`, :attr:`green` and :attr:`blue` if you want a consistent
        representation.

        >>> Color(255, 0, 0).to_tcl()
        '#ff0000'
        >>> Color('red').to_tcl()
        'red'
        >>> Color('red') == Color(255, 0, 0)
        True
        """
        return self._color_string

    # must not compare self._color_string because 'white' and '#ffffff' should
    # be equal
    def __eq__(self, other):
        if isinstance(other, Color):
            return self._rgb == other._rgb
        return NotImplemented

    # equal objects MUST have the same hash, so self._color_string can't be
    # used here
    def __hash__(self):
        return hash(self._rgb)
