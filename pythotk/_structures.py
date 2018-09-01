import abc
import base64
import collections.abc
import functools
import itertools
import sys
import traceback

import pythotk as tk
from pythotk._tcl_calls import needs_main_thread


class Callback:
    """An object that calls functions.

    Example::

        >>> c = Callback()
        >>> c.connect(print, args=["hello", "world"])
        >>> c.run()   # runs print("hello", "world"), usually pythotk does this
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


# this is here because it's used in many places, like most other things
# in this file
on_quit = Callback()


class ConfigDict(collections.abc.MutableMapping):

    def __init__(self):
        # {option: type spec}
        self._types = collections.defaultdict(lambda: str)

        # {option: instruction string}
        self._disabled = {}

    def __repr__(self):
        return '<a config object, behaves like a dict>'

    def __call__(self, *args, **kwargs):
        raise TypeError("use widget.config['option'] = value, "
                        "not widget.config(option=value)")

    @abc.abstractmethod
    def _set(self, option, value):
        """Sets an option to the given value.

        *option* is an option name without a leading dash.
        """

    @abc.abstractmethod
    def _get(self, option, returntype):
        """Returns the value of an option.

        See _set. The returntype should be self._types[option].
        """

    @abc.abstractmethod
    def _list_options(self):
        """Returns an iterable of options that can be passed to _get."""

    def _check_option(self, option):
        # by default, e.g. -tex would be equivalent to -text, but that's
        # disabled to make lookups in self._types and self._disabled
        # easier
        if option in self._disabled:
            raise ValueError("the %r option is not supported, %s instead"
                             % (option, self._disabled[option]))
        if option not in iter(self):    # calls the __iter__
            raise KeyError(option)

    # the type of value is not checked with self._types because python is
    # dynamically typed
    @needs_main_thread
    def __setitem__(self, option, value):
        self._check_option(option)
        self._set(option, value)

    @needs_main_thread
    def __getitem__(self, option):
        self._check_option(option)
        return self._get(option)

    def __delitem__(self, option):
        raise TypeError("options cannot be deleted")

    # __contains__ seems to try doing self[option] and catch KeyError by
    # default, but that doesn't work with disabled options because __getitem__
    # raises ValueError
    def __contains__(self, option):
        try:
            self._check_option(option)
            return True
        except (KeyError, ValueError):
            return False

    def __iter__(self):
        for option in self._list_options():
            if option not in self._disabled:
                yield option

    def __len__(self):
        # this is correct in corner cases
        return len(set(self._list_options()) - self._disabled.keys())


class CgetConfigureConfigDict(ConfigDict):

    def __init__(self, caller_func):
        super().__init__()
        self._caller_func = caller_func

    def _set(self, option, value):
        self._caller_func(None, 'configure', '-' + option, value)

    def _get(self, option):
        return self._caller_func(self._types[option], 'cget', '-' + option)

    def _list_options(self):
        infos = self._caller_func([[str]], 'configure')
        return (info[0].lstrip('-') for info in infos)


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
                   green
                   blue

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
        rgb = tk.tcl_call([int], 'winfo', 'rgb', '.', self._color_string)

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


class TclVar:
    """Represents a global Tcl variable.

    In Tcl, it's possible to e.g. run code when the value of a variable
    changes, or wait until the variable is set. Python's variables can't do
    things like that, so Tcl variables are represented as ``TclVar`` objects
    in Python. If you want to set the value of the variable object,
    ``variable_object = new_value`` doesn't work because that only sets a
    Python variable, and you need ``variable_object.set(new_value)`` instead.
    Similarly, ``variable_object.get()`` returns the value of the Tcl variable.

    Use ``TclVar(name='asd')`` to create a variable object that represents a
    Tcl variable named ``asd``, or ``TclVar()`` to let pythotk choose a
    variable name for you.

    By default, :meth:`get` returns a string. The ``type`` keyword argument
    should be :ref:`a type spec <type-spec>`, and it changes that. For example,
    the :meth:`get` method of ``TclVar(type=int)`` returns an integer.

    .. attribute:: type

        This ``TclVar()`` argument and attribute is a
        :ref:`type spec <type-spec>` of what :meth:`get` returns.
    """

    _default_names = map('pythotk_var_{}'.format, itertools.count(1))

    def __init__(self, *, name=None, type=str):
        if name is None:
            # must use self.__class__ instead of type(self) because type is
            # a local variable here, lol
            name = 'pythotk_var_' + next(self.__class__._default_names)
        self._name = name
        self.type = type
        self._write_trace = None

    def __repr__(self):
        try:
            value_repr = repr(tk.tcl_call(str, 'set', self))
        except tk.TclError:
            value_repr = 'no value has been set'

        return '<%s %r: %s>' % (type(self).__name__, self.to_tcl(), value_repr)

    @classmethod
    def from_tcl(cls, varname):
        """Creates a variable object from a name string.

        See :ref:`type-spec` for details. Note that the :attr:`type` of the
        resulting variable object is ``str``, and you may need to change it.
        """
        return cls(name=varname)

    def to_tcl(self):
        """Returns the variable name as a string."""
        return self._name

    def set(self, new_value):
        """Sets the value of the variable.

        The value does not need to be of the :attr:`type` of the variable; it
        can be anything that can be :ref:`converted to tcl <to-tcl>`.
        """
        tk.tcl_call(None, 'set', self, new_value)

    def get(self):
        """Returns the value of the variable."""
        return tk.tcl_call(self.type, 'set', self._name)

    def wait(self):
        """Waits for this variable to be modified.

        The GUI remains responsive during the waiting. See ``tkwait variable``
        in :man:`tkwait(3tk)` for details.
        """
        tk.tcl_call(None, 'tkwait', 'variable', self)

    @property
    def write_trace(self):
        """
        A :class:`.Callback` that runs when the value of the variable changes.

        The connected functions will be called with one argument, the new
        value. This is implemented with ``trace add variable``, documented in
        :man:`trace(3tcl)`.
        """
        if self._write_trace is None:
            # self.type can change and it is a type spec (not necessarily
            # compatible with isinstance), so must not rely on that
            self._write_trace = Callback(object)

            def runner(*junk):
                self._write_trace.run(self.get())

            command = tk.create_command(runner, [str, str, str])
            tk.tcl_call(None, 'trace', 'add', 'variable',
                        self, 'write', command)

        return self._write_trace


@functools.total_ordering
class ScreenDistance:
    """Represents a Tk screen distance.

    If you don't know or care what screen distances are, use the :attr:`pixels`
    attribute. The ``value`` can be an integer or float of pixels or a string
    that :man:`Tk_GetPixels(3tk)` accepts; for example, ``123`` or ``'2i'``.

    ``ScreenDistance`` objects are hashable, and they can be compared with
    each other:

    >>> funny_dict = {ScreenDistance(1): 'lol'}
    >>> funny_dict[ScreenDistance(1)]
    'lol'
    >>> ScreenDistance('1c') == ScreenDistance('1i')
    False
    >>> ScreenDistance('1c') < ScreenDistance('1i')
    True

    .. attribute:: pixels

        The number of pixels that this screen distance represents as an int.

        This is implemented with ``winfo pixels``, documented in
        :man:`winfo(3tk)`.

    .. attribute:: fpixels

        The number of pixels that this screen distance represents as a float.

        This is implemented with ``winfo fpixels``, documented in
        :man:`winfo(3tk)`.
    """

    def __init__(self, value):
        self._value = str(value)

        # creating a ScreenDistance object must fail if the screen distance
        # is invalid, that's why this is here
        self.pixels = tk.tcl_call(int, 'winfo', 'pixels', '.', self._value)
        self.fpixels = tk.tcl_call(float, 'winfo', 'fpixels', '.', self._value)

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._value)

    # comparing works with integer pixels because floating point errors are
    # not fun
    def __eq__(self, other):
        if not isinstance(other, ScreenDistance):
            return NotImplemented
        return self.pixels == other.pixels

    def __gt__(self, other):
        if not isinstance(other, ScreenDistance):
            return NotImplemented
        return self.pixels > other.pixels

    def __hash__(self):
        return hash(self.fpixels)

    @classmethod
    def from_tcl(cls, value_string):
        """Creates a screen distance object from a Tk screen distance string.

        See :ref:`type-spec` for details.
        """
        return cls(value_string)

    def to_tcl(self):
        """Return the ``value`` as a string."""
        return self._value


def _options(kwargs):
    for name, value in kwargs.items():
        yield ('-from' if name == 'from_' else '-' + name)
        yield value


class Image:
    """Represents a Tk photo image.

    Image objects are wrappers for things documented in :man:`image(3tk)` and
    :man:`photo(3tk)`. They are mutable, so you can e.g. set a label's image to
    an image object and then later change that image object; the label will
    update automatically.

    .. note::
        PNG support was added in Tk 8.6. Use GIF images if you want backwards
        compatibility with Tk 8.5.

    Creating a new ``Image`` object with ``Image(...)`` calls
    ``image create photo`` followed by the options in Tcl. See
    :man:`image(3tk)` for details.

    Keyword arguments are passed as options to :man:`photo(3tk)` as usual,
    except that if a ``data`` keyword argument is given, it should be a
    :class:`bytes` object of data that came from e.g. an image file opened with
    ``'rb'``; it will be automatically converted to base64.

    Image objects can be compared with ``==``, and they compare equal if they
    represent the same Tk image; that is, ``image1 == image2`` returns
    ``image1.to_tcl() == image2.to_tcl()``. Image objects are also hashable.

    .. attribute:: config

        Similar to :ref:`the widget config attribute <options>`.
    """

    def __init__(self, **kwargs):
        if 'data' in kwargs:
            kwargs['data'] = base64.b64encode(kwargs['data']).decode('ascii')
        name = tk.tcl_call(str, 'image', 'create', 'photo', *_options(kwargs))
        self._init_from_name(name)

    def _init_from_name(self, name):
        self._name = name
        self.config = CgetConfigureConfigDict(
            lambda returntype, *args: tk.tcl_call(returntype, self, *args))
        self.config._types.update({
            'data': str,
            'format': str,
            'file': str,
            'gamma': float,
            'width': int,
            'height': int,
            'palette': str,
        })

    @classmethod
    def from_tcl(cls, name):
        """Create a new image object from the name of a Tk image.

        See :ref:`type-spec` for details.
        """
        image = cls.__new__(cls)  # create an instance without calling __init__
        image._init_from_name(name)
        return image

    def to_tcl(self):
        """Returns the Tk name of the image as a string."""
        return self._name

    def __eq__(self, other):
        if not isinstance(other, Image):
            return NotImplemented
        return self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def delete(self):
        """Calls ``image delete`` documented in :man:`image(3tk)`.

        The image object is useless after this, and most things will raise
        :exc:`.TclError`.
        """
        tk.tcl_call(None, 'image', 'delete', self)

    def in_use(self):
        """True if any widget uses this image, or False if not.

        This calls ``image inuse`` documented in :man:`image(3tk)`.
        """
        return tk.tcl_call(bool, 'image', 'inuse', self)

    @classmethod
    def get_all_images(cls):
        """Return all existing images as a list of :class:`.Image` objects."""
        return tk.tcl_call([cls], 'image', 'names')

    def blank(self):
        """See ``imageName blank`` in :man:`photo(3tk)`."""
        tk.tcl_call(None, self, 'blank')

    def copy_from(self, source_image, **kwargs):
        """See ``imageName copy sourceImage`` documented in :man:`photo(3tk)`.

        Options are passed as usual, except that ``from=something`` is invalid
        syntax in Python, so this method supports ``from_=something`` instead.
        If you do ``image1.copy_from(image2)``, the ``imageName`` in
        :man:`photo(3tk)` means ``image1``, and ``sourceImage`` means
        ``image2``.
        """
        tk.tcl_call(None, self, 'copy', source_image, *_options(kwargs))

    def copy(self, **kwargs):
        """
        Create a new image with the same content as this image so that changing
        the new image doesn't change this image.

        This creates a new image and then calls :meth:`copy_from`, so that
        this...
        ::

            image2 = image1.copy()

        ...does the same thing as this::

            image2 = tk.Image()
            image2.copy_from(image1)

        Keyword arguments passed to ``image1.copy()`` are passed to
        ``image2.copy_from()``. This means that it is possible to do some
        things with both :meth:`copy` and :meth:`copy_from`, but :meth:`copy`
        is consistent with e.g. :meth:`list.copy` and :meth:`dict.copy`.
        """
        result = Image()
        result.copy_from(self, **kwargs)
        return result

    @property
    def width(self):
        """The current width of the image as pixels.

        Note that ``image.width`` is different from ``image.config['width']``;
        ``image.width`` changes if the image's size changes, but
        ``image.config['width']`` often represents the width that the image had
        when it was first created. **tl;dr:** Usually it's best to use
        ``image.width`` instead of ``image.config['width']``.
        """
        return tk.tcl_call(int, 'image', 'width', self)

    @property
    def height(self):
        """See :attr:`width`."""
        return tk.tcl_call(int, 'image', 'height', self)

    # TODO: data and put methods, will be hard because passing around binary

    def get(self, x, y):
        """Returns the :class:`.Color` of the pixel at (x,y)."""
        r, g, b = tk.tcl_call([int], self, 'get', x, y)
        return Color(r, g, b)

    def read(self, filename, **kwargs):
        """See ``imageName read filename`` in :man:`photo(3tk)`."""
        tk.tcl_call(None, self, 'read', filename, *_options(kwargs))

    def redither(self):
        """See ``imageName redither`` in :man:`photo(3tk)`."""
        tk.tcl_call(None, self, 'redither')

    def transparency_get(self, x, y):
        """Check if the pixel at (x,y) is transparent, and return a bool.

        The *x* and *y* are pixels, as integers. See
        ``imageName transparency get`` in :man:`photo(3tk)`.
        """
        return tk.tcl_call(bool, self, 'transparency', 'get', x, y)

    def transparency_set(self, x, y, is_transparent):
        """Make the pixel at (x,y) transparent or not transparent.

        See ``imageName transparency set`` in :man:`photo(3tk)` and
        :meth:`transparency_get`.
        """
        tk.tcl_call(None, self, 'transparency', 'set', x, y, is_transparent)

    def write(self, filename, **kwargs):
        """See ``imageName write`` in :man:`photo(3tk)`."""
        tk.tcl_call(None, self, 'write', filename, *_options(kwargs))
