import collections.abc
import re

import teek
from teek._structures import ConfigDict
from teek._tcl_calls import make_thread_safe
from teek._widgets.base import ChildMixin, Widget


Geometry = collections.namedtuple('Geometry', 'width height x y')


class WmMixin:

    @make_thread_safe
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_delete_window = teek.Callback()
        self.on_take_focus = teek.Callback()

        # TODO: delete the commands when they are no longer needed, mem leak
        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_DELETE_WINDOW',
            teek.create_command(self.on_delete_window.run))
        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_TAKE_FOCUS',
            teek.create_command(self.on_take_focus.run))

    def _repr_parts(self):
        result = ['title=' + repr(self.title)]
        if self.wm_state != 'normal':
            result.append('wm_state=' + repr(self.wm_state))
        return result

    # note that these are documented in Toplevel, this is a workaround to get
    # sphinx to show the docs in the correct place while keeping this class
    # as an implementation detail

    @property
    def title(self):
        return self._call(str, 'wm', 'title', self._get_wm_widget())

    @title.setter
    def title(self, new_title):
        self._call(None, 'wm', 'title', self._get_wm_widget(), new_title)

    # a property named 'state' might be confusing, explicit > implicit
    @property
    def wm_state(self):
        return self._call(str, 'wm', 'state', self._get_wm_widget())

    @wm_state.setter
    def wm_state(self, state):
        self._call(None, 'wm', 'state', self._get_wm_widget(), state)

    @property
    def transient(self):
        return self._call(teek.Widget,
                          'wm', 'transient', self._get_wm_widget())

    @transient.setter
    def transient(self, widget):
        self._call(None, 'wm', 'transient', self._get_wm_widget(),
                   widget._get_wm_widget())

    @make_thread_safe
    def geometry(self, width=None, height=None, x=None, y=None):
        if isinstance(width, str):    # for tkinter users
            raise TypeError("use widget.geometry(width, height) instead of "
                            "widget.geometry(string)")

        if (width is None) ^ (height is None):
            raise TypeError("specify both width and height, or neither")
        if (x is None) ^ (y is None):
            raise TypeError("specify both x and y, or neither")

        if x is y is width is height is None:
            string = self._call(str, 'wm', 'geometry', self._get_wm_widget())
            match = re.search(r'^(\d+)x(\d+)\+(\d+)\+(\d+)$', string)
            return Geometry(*map(int, match.groups()))

        if x is y is None:
            string = '%dx%d' % (width, height)
        elif width is height is None:
            string = '+%d+%d' % (x, y)
        else:
            string = '%dx%d+%d+%d' % (width, height, x, y)
        self._call(None, 'wm', 'geometry', self._get_wm_widget(), string)

    @property
    def minsize(self):
        return self._call((int, int), 'wm', 'minsize', self._get_wm_widget())

    @minsize.setter
    def minsize(self, size):
        width, height = size
        self._call(None, 'wm', 'minsize', self._get_wm_widget(), width, height)

    @property
    def maxsize(self):
        return self._call((int, int), 'wm', 'maxsize', self._get_wm_widget())

    @maxsize.setter
    def maxsize(self, size):
        width, height = size
        self._call(None, 'wm', 'maxsize', self._get_wm_widget(), width, height)

    def iconphoto(self, *images):
        self._call(None, 'wm', 'iconphoto', self._get_wm_widget(), *images)

    def withdraw(self):
        self._call(None, 'wm', 'withdraw', self._get_wm_widget())

    def iconify(self):
        self._call(None, 'wm', 'iconify', self._get_wm_widget())

    def deiconify(self):
        self._call(None, 'wm', 'deiconify', self._get_wm_widget())

    def wait_window(self):
        self._call(None, 'tkwait', 'window', self)

    # to be overrided
    def _get_wm_widget(self):   # pragma: no cover
        raise NotImplementedError


class Toplevel(WmMixin, Widget):
    """This represents a *non-Ttk* ``toplevel`` widget.

    Usually it's easiest to use :class:`Window` instead. It behaves like a
    ``Toplevel`` widget, but it's actually a ``Toplevel`` with a ``Frame``
    inside it.

    Manual page: :man:`toplevel(3tk)`

    .. method:: geometry(width=None, height=None, x=None, y=None)

        Set or get the size and place of the window in pixels.

        Tk's geometries are strings like ``'100x200+300+400'``, but that's not
        very pythonic, so this method works with integers and namedtuples
        instead. This method can be called in a few different ways:

        * If *width* and *height* are given, the window is resized.
        * If *x* and *y* are given, the window is moved.
        * If all arguments are given, the window is resized and moved.
        * If no arguments are given, the current geometry is
          returned as a namedtuple with *width*, *height*, *x* and
          *y* fields.
        * Calling this method otherwise raises an error.

        Examples::

            >>> import teek
            >>> window = teek.Window()
            >>> window.geometry(300, 200)    # resize to 300px wide, 200px high
            >>> window.geometry(x=0, y=0)    # move to upper left corner
            >>> window.geometry()            # doctest: +SKIP
            Geometry(width=300, height=200, x=0, y=0)
            >>> window.geometry().width      # doctest: +SKIP
            300

        See also ``wm geometry`` in :man:`wm(3tk)`.

    .. method:: iconphoto(*images, default=False)

        Calls ``wm iconphoto`` documented in :man:`wm(3tk)`.

        Positional arguments should be :class:`.Image` objects. If
        ``default=True`` is given, the ``-default`` switch is used; otherwise
        it isn't.

    .. attribute:: title
                   wm_state
                   transient
                   minsize
                   maxsize
    .. method:: withdraw()
                iconify()
                deiconify()

        These attributes and methods correspond to similarly named things in
        :man:`wm(3tk)`. Note that ``wm_state`` is ``state`` in the manual page;
        the teek attribute is ``wm_state`` to make it explicit that it is
        the wm state, not some other state.

        All of the attributes are settable, so you can do e.g.
        ``my_toplevel.title = "lol"``. Here are the types of the attributes:

        * ``title`` and ``wm_state`` are strings.
        * ``transient`` is a widget.
        * ``minsize`` and ``maxsize`` are tuples of two integers.

        .. note::
            If ``transient`` is set to a :class:`.Window`, looking it up won't
            give back that same window; instead, it gives the
            :attr:`~.Window.toplevel` of the window.

    .. method:: wait_window()

        Waits until the window is destroyed with :meth:`~Widget.destroy`.

        This method blocks until the window is destroyed, but it can still be
        called from the :ref:`event loop <eventloop>`; behind the covers, it
        runs another event loop that makes the GUI not freeze.

        See ``tkwait window`` in :man:`tkwait(3tk)` for more details.

    .. attribute:: on_delete_window
                   on_take_focus

        :class:`Callback` objects that run with no arguments when a
        ``WM_DELETE_WINDOW`` or ``WM_TAKE_FOCUS`` event occurs. See
        :man:`wm(3tk)`. These are connected to nothing by default.
    """

    _widget_name = 'toplevel'
    tk_class_name = 'Toplevel'

    # this allows passing title as a positional argument
    @make_thread_safe
    def __init__(self, title=None, **options):
        # toplevel(3tk): "[...] it must be the window identifier of a container
        # window, specified as a hexadecimal string [...]"
        if 'use' in options and isinstance(options['use'], int):
            options['use'] = hex(options['use'])

        super().__init__(None, **options)
        if title is not None:
            self.title = title

    def _init_config(self):
        super()._init_config()

        # "didn't bother" ones are more work than they are worth because nobody
        # will use them anyway
        self.config._types.update({
            'colormap': str,    # 'new' or a widget name, didn't bother
            'container': bool,
            'height': teek.ScreenDistance,
            'menu': teek.Menu,
            'screen': str,
            'use': int,
            'visual': str,      # didn't bother
            'width': teek.ScreenDistance,
        })

    def _get_wm_widget(self):
        return self


# allow accessing Toplevel config things like 'menu' through the Window widget
class FallbackConfigDict(ConfigDict):

    def __init__(self, main_config, fallback_config):
        super().__init__()

        # this doesn't need a ChainMap because self._types isn't changed
        # after this
        self._types.update(main_config._types)
        self._types.update(fallback_config._types)

        self._main_config = main_config
        self._fallback_config = fallback_config

    def _set(self, option, value):
        if option in self._main_config._list_options():
            self._main_config._set(option, value)
        else:
            self._fallback_config._set(option, value)

    def _get(self, option):
        if option in self._main_config._list_options():
            return self._main_config._get(option)
        else:
            return self._fallback_config._get(option)

    def _list_options(self):
        return (set(self._main_config._list_options()) |
                set(self._fallback_config._list_options()))


class Window(WmMixin, Widget):
    """A convenient widget that represents a Ttk frame inside a toplevel.

    Tk's windows like :class:`Toplevel` are *not* Ttk widgets, and there are no
    Ttk window widgets. If you add Ttk widgets to Tk windows like
    :class:`Toplevel` so that the widgets don't fill the entire window, your
    GUI looks messy on some systems, like my linux system with MATE desktop.
    This is why you should always create a big Ttk frame that fills the window,
    and then add all widgets into that frame. That's kind of painful and most
    people don't bother with it, but this class does that for you, so you can
    just create a :class:`Window` and add widgets to that.

    All initialization arguments are passed to :class:`Toplevel`.

    The :attr:`~.Widget.config` attribute combines options from the
    :class:`.Frame` and the :class:`.Toplevel` so that it uses :class:`.Frame`
    options whenever they are available, and :class:`.Toplevel` options
    otherwise. For example, :class:`.Frame` has an option named ``'width'``, so
    ``some_window.config['width']`` uses that, but frames don't have a
    ``'menu'`` option, so ``some_window.config['menu']`` uses the toplevel's
    menu option.

    There is no manual page for this class because this is purely a teek
    feature; there is no ``window`` widget in Tk.

    .. seealso:: :class:`Toplevel`, :class:`Frame`

    .. attribute:: toplevel

        The :class:`Toplevel` widget that the frame is in. The :class:`Window`
        object itself has all the attributes and methods of the :class:`Frame`
        inside the window, and for convenience, also many :class:`Toplevel`
        things like :attr:`~Toplevel.title`, :meth:`~Toplevel.withdraw` and
        :attr:`~Toplevel.on_delete_window`.
    """

    _widget_name = 'ttk::frame'
    tk_class_name = None

    @make_thread_safe
    def __init__(self, *args, **kwargs):
        self.toplevel = Toplevel(*args, **kwargs)
        super().__init__(self.toplevel)     # calls self._init_config()

        self.config = FallbackConfigDict(self.config, self.toplevel.config)
        ChildMixin.pack(self, fill='both', expand=True)

    def destroy(self):
        """Destroys the :attr:`.toplevel` and the frame in it.

        This overrides :meth:`.Widget.destroy`.
        """
        self.toplevel.destroy()

    def _destroy_recurser(self):
        super().destroy()

    def _init_config(self):
        # if you change these, also change Frame's types in misc.py
        self.config._types.update({
            'height': teek.ScreenDistance,
            'padding': teek.ScreenDistance,
            'width': teek.ScreenDistance,
        })

    def _get_wm_widget(self):
        return self.toplevel
