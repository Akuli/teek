import collections.abc
import re

import pythotk as tk
from pythotk._widgets.base import ChildMixin, Widget


Geometry = collections.namedtuple('Geometry', 'width height x y')


class WmMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_delete_window = tk.Callback()
        self.on_delete_window.connect(tk.quit)
        self.on_take_focus = tk.Callback()

        # TODO: delete the commands when they are no longer needed, mem leak
        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_DELETE_WINDOW',
            tk.create_command(self.on_delete_window.run))
        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_TAKE_FOCUS',
            tk.create_command(self.on_take_focus.run))

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

    def geometry(self, width=None, height=None, x=None, y=None):
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

    def withdraw(self):
        self._call(None, 'wm', 'withdraw', self._get_wm_widget())

    def iconify(self):
        self._call(None, 'wm', 'iconify', self._get_wm_widget())

    def deiconify(self):
        self._call(None, 'wm', 'deiconify', self._get_wm_widget())

    def wait_window(self):
        self._call(None, 'tkwait', 'window', self)

    # to be overrided
    def _get_wm_widget(self):
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

            >>> import pythotk as tk
            >>> window = tk.Window()
            >>> window.geometry(300, 200)    # resize to 300px wide, 200px high
            >>> window.geometry(x=0, y=0)    # move to upper left corner
            >>> window.geometry()            # doctest: +SKIP
            Geometry(width=300, height=200, x=0, y=0)
            >>> window.geometry().width      # doctest: +SKIP
            300

        See also ``wm geometry`` in :man:`wm(3tk)`.

    .. attribute:: title
                   wm_state
    .. method:: geometry(width=None, height=None, x=None, y=None)
                withdraw()
                iconify()
                deiconify()

        These attributes and methods correspond to similarly named things in
        :man:`wm(3tk)`. Note that ``wm_state`` is ``state`` in the manual page;
        the pythotk attribute is ``wm_state`` to make it explicit that it is
        the wm state, not some other state.

        ``title`` and ``wm_state`` are strings, and they can be set like
        ``my_toplevel.title = "Hello"``.

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
        :man:`wm(3tk)`.

        By default, ``some_window.on_delete_window`` is connected to
        :func:`pythotk.quit`.
    """

    # allow passing title as a positional argument
    def __init__(self, title=None, **options):
        # toplevel(3tk): "[...] it must be the window identifier of a container
        # window, specified as a hexadecimal string [...]"
        if 'use' in options and isinstance(options['use'], int):
            options['use'] = hex(options['use'])

        super().__init__('toplevel', None, **options)

        # "didn't bother" ones are more work than they are worth because nobody
        # will use them anyway
        self.config._types.update({
            'colormap': str,    # 'new' or a widget name, didn't bother
            'container': bool,
            'menu': Widget,  # TODO: should be Menu, but Menu doesn't exist yet
            'screen': str,
            'use': int,
            'visual': str,      # didn't bother
        })
        if title is not None:
            self.title = title

    def _get_wm_widget(self):
        return self

    @classmethod
    def from_widget_path(cls, path_string):
        raise NotImplementedError


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

    There is no manual page for this class because this is purely a pythotk
    feature; there is no ``window`` widget in Tk.

    .. seealso:: :class:`Toplevel`, :class:`Frame`

    .. attribute:: toplevel

        The :class:`Toplevel` widget that the frame is in. The :class:`Window`
        object itself has all the attributes and methods of the :class:`Frame`
        inside the window, and for convenience, also many :class:`Toplevel`
        things like :attr:`~Toplevel.title`, :meth:`~Toplevel.withdraw` and
        :attr:`~Toplevel.on_delete_window`.
    """

    def __init__(self, *args, **kwargs):
        self.toplevel = Toplevel(*args, **kwargs)
        super().__init__('ttk::frame', self.toplevel)
        self.config._types.update({
            'padding': tk.ScreenDistance,
        })
        ChildMixin.pack(self, fill='both', expand=True)

    def _get_wm_widget(self):
        return self.toplevel
