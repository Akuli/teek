import collections.abc
import re
from _tkinter import TclError

import pythotk
from pythotk import _tcl_calls, _structures

_widgets = {}
_tcl_calls.on_quit.connect(_widgets.clear)


# make things more tkinter-user-friendly
def _tkinter_hint(good, bad):
    def dont_use_this(self, *args, **kwargs):
        raise TypeError("use %s, not %s" % (good, bad))

    return dont_use_this


class ConfigDict(collections.abc.MutableMapping):

    def __init__(self, caller):
        self._call = caller
        self._types = {}      # {option: argument for run}  str is default
        self._disabled = {}   # {option: instruction string}

    def __repr__(self):
        return '<a config object, behaves like a dict>'

    __call__ = _tkinter_hint("widget.config['option'] = value",
                             "widget.config(option=value)")

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
    def __setitem__(self, option, value):
        self._check_option(option)
        self._call(None, 'configure', '-' + option, value)

    def __getitem__(self, option):
        self._check_option(option)
        returntype = self._types.get(option, str)
        return self._call(returntype, 'cget', '-' + option)

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
        # [[str]] is a 2d list of strings
        for info in self._call([[str]], 'configure'):
            option = info[0].lstrip('-')
            if option not in self._disabled:
                yield option

    def __len__(self):
        # FIXME: this is wrong if one of the disableds not exists, hard 2 test
        options = self._call([[str]], 'configure')
        return len(options) - len(self._disabled)


class Widget:
    """This is a base class for all widgets.

    All widgets inherit from this class, and they have all the attributes
    and methods documented here.

    Don't create instances of ``Widget`` yourself like ``Widget(...)``; use one
    of the classes documented below instead. However, you can use ``Widget``
    with :func:`isinstance`; e.g. ``isinstance(thingy, tk.Widget)`` returns
    ``True`` if ``thingy`` is a pythotk widget.

    .. attribute:: config

        A dict-like object that represents the widget's options.

        >>> window = tk.Window()
        >>> label = tk.Label(window, text='Hello World')
        >>> label.config
        <a config object, behaves like a dict>
        >>> label.config['text']
        'Hello World'
        >>> label.config['text'] = 'New Text'
        >>> label.config['text']
        'New Text'
        >>> label.config.update({'text': 'Even newer text'})
        >>> label.config['text']
        'Even newer text'
        >>> import pprint
        >>> pprint.pprint(dict(label.config))       # prints everything nicely
        ... # doctest: +ELLIPSIS
        {...,
         'text': 'Even newer text',
         ...}
    """

    def __init__(self, widgetname, parent, **options):
        if parent is None:
            parentpath = ''
        else:
            parentpath = parent.to_tcl()
        self.parent = parent

        # use some_widget.to_tcl() to access some_widget._widget_path
        counter = _tcl_calls.counts[widgetname]
        self._widget_path = '%s.%s%d' % (parentpath, widgetname, next(counter))

        # TODO: some config options can only be given when the widget is
        # created, add support for them
        self._call(None, widgetname, self.to_tcl())
        _widgets[self.to_tcl()] = self

        self.config = ConfigDict(
            lambda returntype, *args: self._call(returntype, self, *args))
        self._init_config()
        self.config.update(options)

    # see _tcl_calls.call
    @classmethod
    def from_tcl(cls, path_string):
        """Creates a widget from a Tcl path names.

        In Tcl, widgets are represented as commands, and doing something to the
        widget invokes the command. Use this method if you know the Tcl command
        and you would like to have a widget object instead.

        This method raises :exc:`TypeError` if it's called from a different
        ``Widget`` subclass than what the type of the ``path_string`` widget
        is:

        >>> window = tk.Window()
        >>> tk.Button.from_tcl(tk.Label(window).to_tcl())  # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: '...' is a Label, not a Button
        """
        if path_string == '.':
            # this kind of sucks, i might make a _RootWindow class later
            return None

        result = _widgets[path_string]
        if not isinstance(result, cls):
            raise TypeError("%r is a %s, not a %s" % (
                path_string, type(result).__name__, cls.__name__))
        return result

    def to_tcl(self):
        """Returns the widget's Tcl command name. See :meth:`from_tcl`."""
        return self._widget_path

    # TODO: is this used anywhere??
    def _init_config(self):
        pass

    def __repr__(self):
        class_name = type(self).__name__
        if getattr(pythotk, class_name, None) is type(self):
            result = 'pythotk.%s widget' % class_name
        else:
            result = '{0.__module__}.{0.__name__} widget'.format(type(self))

        if not self.winfo_exists():
            # _repr_parts() doesn't need to work with destroyed widgets
            return '<destroyed %s>' % result

        parts = self._repr_parts()
        if parts:
            result += ': ' + ', '.join(parts)
        return '<' + result + '>'

    def _repr_parts(self):
        # overrided in subclasses
        return []

    __getitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    __setitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    cget = _tkinter_hint("widget.config['option']", "widget.cget('option')")
    configure = _tkinter_hint("widget.config['option'] = value",
                              "widget.configure(option=value)")

    # like _tcl_calls.call, but with better error handling
    def _call(self, *args, **kwargs):
        try:
            return _tcl_calls.call(*args, **kwargs)
        except TclError as err:
            if not self.winfo_exists():
                raise RuntimeError("the widget has been destroyed") from None
            raise err

    def destroy(self):
        """Delete this widget and all child widgets.

        Manual page: :man:`destroy(3tk)`
        """
        for name in self._call([str], 'winfo', 'children', self):
            # allow overriding the destroy() method if the widget was
            # created by pythotk
            if name in _widgets:
                _widgets[name].destroy()
            else:
                self._call(None, 'destroy', name)

        self._call(None, 'destroy', self)
        del _widgets[self.to_tcl()]

    def winfo_children(self):
        """Returns a list of child widgets that this widget has.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call([Widget], 'winfo', 'children', self)

    def winfo_exists(self):
        """Returns False if the widget has been destroyed. See :meth:`destroy`.

        Manual page: :man:`winfo(3tk)`
        """
        # self._call uses this, so this must not use that
        return _tcl_calls.call(bool, 'winfo', 'exists', self)

    def winfo_toplevel(self):
        """Returns the :class:`Toplevel` widget that this widget is in.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(Widget, 'winfo', 'toplevel', self)


Geometry = collections.namedtuple('Geometry', 'width height x y')


class _WmMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_delete_window = _structures.Callback()
        self.on_delete_window.connect(pythotk.quit)
        self.on_take_focus = _structures.Callback()

        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_DELETE_WINDOW',
            _tcl_calls.create_command(self.on_delete_window.run))
        self._call(
            None, 'wm', 'protocol', self._get_wm_widget(), 'WM_TAKE_FOCUS',
            _tcl_calls.create_command(self.on_take_focus.run))

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

    # to be overrided
    def _get_wm_widget(self):
        raise NotImplementedError


class Toplevel(_WmMixin, Widget):
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
    .. attribute:: wm_state
    .. method:: geometry(width=None, height=None, x=None, y=None)
    .. method:: withdraw()
    .. method:: iconify()
    .. method:: deiconify()

        These attributes and methods correspond to similarly named things in
        :man:`wm(3tk)`. Note that ``wm_state`` is ``state`` in the manual page;
        the pythotk attribute is ``wm_state`` to make it explicit that it is
        the wm state, not some other state.

        ``title`` and ``wm_state`` are strings, and they can be set like
        ``my_toplevel.title = "Hello"``.

    .. attribute:: on_delete_window
    .. attribute:: on_take_focus

        :class:`Callback` objects that run with no arguments when a
        ``WM_DELETE_WINDOW`` or ``WM_TAKE_FOCUS`` event occurs. See
        :man:`wm(3tk)`.

        By default, ``some_window.on_delete_window`` is connected to
        :func:`pythotk.quit`.
    """

    # allow passing title as a positional argument
    def __init__(self, title=None, **options):
        super().__init__('toplevel', None, **options)
        if title is not None:
            self.title = title

    def _get_wm_widget(self):
        return self

    @classmethod
    def from_widget_path(cls, path_string):
        raise NotImplementedError


class Window(_WmMixin, Widget):
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
        ChildMixin.pack(self, fill='both', expand=True)

    def _get_wm_widget(self):
        return self.toplevel


class ChildMixin:

    def pack(self, **kwargs):
        args = []
        for name, value in kwargs.items():
            args.append('-' + name.rstrip('_'))   # e.g. in_
            args.append(value)
        self._call(None, 'pack', self.to_tcl(), *args)

    def pack_forget(self):
        self._call(None, 'pack', 'forget', self.to_tcl())

    def pack_info(self):
        # TODO: add some way to specify a separate type for each key
        raw_result = self._call({str: str}, 'pack', 'info', self.to_tcl())
        result = {}

        for key, value in raw_result.items():
            if key in ('padx', 'pady', 'ipadx', 'ipady'):
                result[key] = int(value)
            elif key == 'expand':
                result[key] = bool(int(value))
            elif key == 'in':
                result[key] = _widgets[value]
            else:
                result[key] = value

        return result


class Frame(ChildMixin, Widget):
    """An empty widget. Frames are often used as containers for other widgets.

    Manual page: :man:`ttk_frame(3tk)`
    """

    def __init__(self, parent, **options):
        super().__init__('ttk::frame', parent, **options)


class Separator(ChildMixin, Widget):
    """A horizontal or vertical line, depending on an ``orient`` option.

    Create a horizontal separator like this...
    ::

        separator = tk.Separator(some_widget, orient='horizontal')
        separator.pack(fill='x')    # default is side='top'

    ...and create a vertical separator like this::

        separator = tk.Separator(some_widget, orient='vertical')
        separator.pack(fill='y', side='left')   # can also use side='right'

    Manual page: :man:`ttk_separator(3tk)`
    """
    # TODO: link to pack docs

    def __init__(self, parent, **options):
        super().__init__('ttk::separator', parent, **options)


class Label(ChildMixin, Widget):
    """A widget that displays text.

    For convenience, the ``text`` option can be also given as a positional
    initialization argument, so ``tk.Label(parent, "hello")`` and
    ``tk.Label(parent, text="hello")`` do the same thing.

    Manual page: :man:`ttk_label(3tk)`
    """

    def __init__(self, parent, text='', **kwargs):
        super().__init__('ttk::label', parent, text=text, **kwargs)

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]


class Button(ChildMixin, Widget):
    """A widget that runs a callback when it's clicked.

    ``text`` can be given as with :class:`Label`. If ``command`` is given, it
    should be a function that will be called with no arguments when the button
    is clicked. This...
    ::

        button = tk.Button(some_widget, "Click me", do_something)

    ...does the same thing as this::

        button = tk.Button(some_widget, "Click me")
        button.on_click.connect(do_something)

    Manual page: :man:`ttk_button(3tk)`

    .. attribute:: on_click

        A :class:`Callback` that runs when the button is clicked.
    """

    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__('ttk::button', parent, text=text, **kwargs)
        self.on_click = _structures.Callback()
        self.config['command'] = _tcl_calls.create_command(self.on_click.run)
        self.config._disabled['command'] = ("use the on_click attribute " +
                                            "or an initialization argument")
        if command is not None:
            self.on_click.connect(command)

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]

    def invoke(self):
        self._call(None, self, 'invoke')


'''
class _SelectedIndexesView(abcoll.MutableSet):
    """A set-like view of currently selected indexes.

    Negative and out-of-range indexes are not allowed.
    """

    def __init__(self, listbox):
        self._listbox = listbox

    def __repr__(self):
        return '<Listbox selected_indexes view: %s>' % repr(set(self))

    def __iter__(self):
        return iter(pythotk.tk.call(self._listbox.to_tcl(), 'curselection'))

    def __len__(self):
        return len(pythotk.tk.call(self._listbox.to_tcl(), 'curselection'))

    def __contains__(self, index):
        return bool(pythotk.tk.call(
            self._listbox.to_tcl(), 'selection', 'includes', index))

    def add(self, index):
        """Select an index in the listbox if it's not currently selected."""
        if index not in range(len(self._listbox)):
            raise ValueError("listbox index %r out of range" % (index,))
        pythotk.tk.call(self._listbox.to_tcl(), 'selection', 'set', index)

    def discard(self, index):
        """Unselect an index in the listbox if it's currently selected."""
        if index not in range(len(self._listbox)):
            raise ValueError("listbox index %r out of range" % (index,))
        pythotk.tk.call(self._listbox.to_tcl(), 'selection', 'clear', index)

    # abcoll.MutableSet doesn't implement this :(
    def update(self, items):
        for item in items:
            self.add(item)


class _SelectedItemsView(abcoll.MutableSet):
    """A view of currently selected items as strings.

    The items are ordered. Iterating over the view yields the same
    element more than once if it's in the listbox more than once.
    """

    def __init__(self, listbox, indexview):
        self._listbox = listbox
        self._indexview = indexview

    def __repr__(self):
        return '<Listbox selected_items view: %s>' % repr(set(self))

    # this is used when we need to get rid of duplicates anyway
    def _to_set(self):
        return {self._listbox[index] for index in self._indexview}

    def __iter__(self):
        return iter(self._to_set())

    def __len__(self):
        return len(self._to_set())

    def __contains__(self, item):
        return item in self._to_set()

    def add(self, item):
        """Select all items equal to *item* in the listbox."""
        # sequence.index only returns first matching index :(
        for index, item2 in enumerate(self._listbox):
            if item == item2:
                self._indexview.add(index)

    def discard(self, item):
        """Unselect all items equal to *item* in the listbox."""
        for index, item2 in enumerate(self._listbox):
            if item == item2:
                self._indexview.discard(index)


class Listbox(ChildMixin, Widget, abcoll.MutableSequence):

    def __init__(self, parent, *, multiple=False, **kwargs):
        super().__init__('listbox', parent, **kwargs)
        self.selected_indexes = _SelectedIndexesView(self)
        self.selected_items = _SelectedItemsView(self, self.selected_indexes)

    def __len__(self):
        return pythotk.tk.call(self.to_tcl(), 'index', 'end')

    def _fix_index(self, index):
        if index < 0:
            index += len(self)
        if index not in range(len(self)):
            raise IndexError("listbox index %d out of range" % index)
        return index

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        return pythotk.tk.call(self.to_tcl(), 'get', self._fix_index(index))

    def __delitem__(self, index):
        if isinstance(index, slice):
            # these need to be deleted in reverse because deleting
            # something changes all indexes after it
            indexes = list(range(*index.indices(len(self))))
            indexes.sort(reverse=True)
            for i in indexes:
                del self[i]

        pythotk.tk.call(self.to_tcl(), 'delete', self._fix_index(index))

    def __setitem__(self, index, item):
        if isinstance(index, slice):
            # this is harder than you might think
            #   >>> stuff = ['a', 'b', 'c', 'd', 'e']
            #   >>> stuff[4:2] = ['x', 'y', 'z']
            #   >>> stuff
            #   ['a', 'b', 'c', 'd', 'x', 'y', 'z', 'e']
            #   >>>
            # that's slicing with step 1, now imagine step -2
            raise TypeError("assigning to slices is not supported")

        if self[index] == item:
            # shortcut
            return

        index = self._fix_index(index)
        was_selected = (index in self.selected_indexes)
        del self[index]
        self.insert(index, item)
        if was_selected:
            self.selected_indexes.add(index)

    def insert(self, index, item):
        # this doesn't use _fix_index() because this must handle out of
        # range indexes differently, like list.insert does
        if index > len(self):
            index = len(self)
        if index < -len(self):
            index = -len(self)
        if index < 0:
            index += len(self)
        assert 0 <= index <= len(self)
        pythotk.tk.call(self.to_tcl(), 'insert', index, item)
'''
