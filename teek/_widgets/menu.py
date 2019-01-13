import collections.abc

import teek as tk
from teek._structures import CgetConfigureConfigDict
from teek._tcl_calls import make_thread_safe
from teek._widgets.base import Widget


# all menu item things that do something run in the main thread to avoid any
# kind of use of menu items that are in an inconsistent state, and the Menu
# class also does this... think of it as poor man's locking or something
class MenuItem:
    """
    Represents an item of a menu. See :ref:`creating-menu-items` for details
    about the arguments.

    Tk's manual pages call these things "menu entries" instead of "menu items",
    but I called them items to avoid confusing these with :class:`.Entry`.

    There are two kinds of :class:`.MenuItem` objects:

    * Menu items that are not in any :class:`.Menu` widget because they haven't
      been added to a menu yet, or they have been removed from a menu. Trying
      to do something with these menu items will likely raise a
      :class:`.RuntimeError`.
    * Menu items that are currently in a :class:`.Menu`.

    Here's an example:

    >>> item = tk.MenuItem("Click me", print)
    >>> item.config['label'] = "New text"
    Traceback (most recent call last):
        ...
    RuntimeError: the MenuItem hasn't been added to a Menu yet
    >>> menu = tk.Menu()
    >>> menu.append(item)
    >>> item.config['label'] = "New text"
    >>> item.config['label']
    'New text'

    .. attribute:: config

        This attribute is similar to :attr:`.Widget.config`. See
        ``MENU ENTRY OPTIONS`` in :man:`menu(3tk)`.

        The types of the values are the same as for similar widgets. For
        example, the ``'command'`` of a :class:`.Button` widget is a
        :class:`.Callback` object connected to a function passed to
        :class:`.Button`, and so is the ``'command'`` of
        ``tk.MenuItem("Click me", some_function)``.

    .. attribute:: type

        This is a string. Currently the possible values are
        ``'separator'``, ``'checkbutton'``, ``'command'``, ``'cascade'`` and
        ``'radiobutton'`` as documented :ref:`above <creating-menu-items>`.
        Don't set this attribute yourself.
    """

    def __init__(self, *args, **kwargs):
        self._options = kwargs.copy()

        if not args:
            self.type = 'separator'
        elif len(args) == 2:
            self._options['label'], second_object = args
            if isinstance(second_object, tk.BooleanVar):
                self.type = 'checkbutton'
                self._options['variable'] = second_object
            elif callable(second_object):
                self.type = 'command'
                self._command_callback = second_object  # see _adding_finalizer
            elif isinstance(second_object, Menu):
                self.type = 'cascade'
                self._options['menu'] = second_object
            else:   # assume an iterable
                self.type = 'cascade'
                self._options['menu'] = Menu(second_object)
        elif len(args) == 3:
            self.type = 'radiobutton'
            (self._options['label'],
             self._options['variable'],
             self._options['value']) = args
        else:
            raise TypeError(
                "expected 0, 2 or 3 arguments to MenuItem, got %d" % len(args))

        self._args = args
        self._kwargs = kwargs
        self._menu = None
        self._index = None

        self.config = CgetConfigureConfigDict(self._config_entrycommand_caller)
        self.config._types.update({
            'activebackground': tk.Color,
            'activeforeground': tk.Color,
            'accelerator': str,
            'background': tk.Color,
            #'bitmap': ???,
            'columnbreak': bool,
            'compound': str,
            'font': tk.Font,
            'foreground': tk.Color,
            'hidemargin': bool,
            'image': tk.Image,
            'indicatoron': bool,
            'label': str,
            'menu': Menu,
            'offvalue': bool,
            'onvalue': bool,
            'selectcolor': tk.Color,
            'selectimage': tk.Image,
            'state': str,
            'underline': bool,
            'value': str,
            'variable': (tk.BooleanVar if self.type == 'checkbutton'
                         else tk.StringVar),
        })
        self.config._special['command'] = self._create_command

    def __repr__(self):
        parts = ['type=%r' % self.type]
        if self._menu is None:
            parts.append("not added to a menu yet")
        else:
            parts.append("added to a menu")

        return '<%s%r: %s>' % (type(self).__name__, self._args,
                               ', '.join(parts))

    def _prepare_adding(self):
        if self._menu is not None:
            raise RuntimeError(
                "cannot add a MenuItem to two different menus "
                "or twice to the same menu")

    def _after_adding(self, menu, index):
        self._menu = menu
        self._index = index
        self.config.update(self._options)
        if self.type == 'command':
            self.config['command'].connect(self._command_callback)

    def _after_removing(self):
        self._menu = None
        self._index = None

    def _check_in_menu(self):
        assert (self._menu is None) == (self._index is None)
        if self._menu is None:
            raise RuntimeError("the MenuItem hasn't been added to a Menu yet")

    @make_thread_safe
    def _config_entrycommand_caller(self, returntype, subcommand, *args):
        assert subcommand in {'cget', 'configure'}
        self._check_in_menu()
        return tk.tcl_call(returntype, self._menu, 'entry' + subcommand,
                           self._index, *args)

    def _create_command(self):
        self._check_in_menu()
        result = tk.Callback()
        command_string = tk.create_command(result.run)
        tk.tcl_call(None, self._menu, 'entryconfigure', self._index,
                    '-command', command_string)
        self._menu.command_list.append(command_string)
        return result


# does not use ChildMixin because usually it's a bad idea to e.g. pack a menu
# TODO: document that this class assumes that nothing else changes the
#       underlying Tcl widget
class Menu(Widget, collections.abc.MutableSequence):
    """This is the menu widget.

    The ``items`` should be an iterable of :class:`.MenuItem` objects, and it's
    treated so that this...
    ::

        menu = tk.Menu([
            tk.MenuItem("Click me", print),
            tk.MenuItem("No, click me instead", print),
        ])

    ...does the same thing as this::

        menu = tk.Menu()
        menu.append(tk.MenuItem("Click me", print))
        menu.append(tk.MenuItem("No, click me instead", print))

    Menu widgets behave like lists of menu items, so if you can do something to
    a list of :class:`.MenuItem` objects, you can probably do it directly to a
    :class:`.Menu` widget as well.

    However, menu widgets don't support slicing, like lists do:

    >>> menu = tk.Menu([
    ...     tk.MenuItem("Click me", print),
    ... ])
    >>> menu.append(tk.MenuItem("No, click me instead", print))
    >>> menu
    <teek.Menu widget: contains 2 items>
    >>> menu[0]     # this works
    <MenuItem('Click me', <built-in function print>): type='command', added to\
 a menu>
    >>> for item in menu:   # this works
    ...     print(item)
    ...
    <MenuItem('Click me', <built-in function print>): type='command', added to\
 a menu>
    <MenuItem('No, click me instead', <built-in function print>): type='comman\
d', added to a menu>
    >>> menu[:2]    # but this doesn't work
    Traceback (most recent call last):
      ...
    TypeError: slicing a Menu widget is not supported
    >>> list(menu)[:2]    # workaround      # doctest: +ELLIPSIS
    [<MenuItem(...): ...>, <MenuItem(...): ...>]

    :class:`.Menu` objects assume that nothing changes the underlying Tk menu
    widget without the :class:`.Menu` object. For example:

    >>> menu = tk.Menu()
    >>> command = menu.to_tcl()
    >>> command      # doctest: +SKIP
    '.menu1'
    >>> # DON'T DO THIS, this is a bad idea
    >>> tk.tcl_eval(None, '%s add checkbutton -command {puts hello}' % command)
    >>> len(menu)   # the menu widget doesn't know that we added an item
    0

    If you don't know what :func:`.tcl_eval` does, you don't need to worry
    about doing this accidentally.

    Manual page: :man:`menu(3tk)`
    """

    _widget_name = 'menu'
    tk_class_name = 'Menu'

    def __init__(self, items=(), **kwargs):
        kwargs.setdefault('tearoff', False)
        super().__init__(None, **kwargs)
        self._items = []
        self.extend(items)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'selectcolor': tk.Color,
            'tearoff': bool,
            'title': str,
            'type': str,
        })

    def _repr_parts(self):
        return ['contains %d items' % len(self)]

    @make_thread_safe
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")
        return self._items[index]

    @make_thread_safe
    def __delitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        index = range(len(self))[index]    # handle indexes like python does it
        self._call(None, self, 'delete', index)
        item = self._items.pop(index)
        item._after_removing()

        # indexes after the deleted item are messed up
        for index in range(index, len(self._items)):
            self._items[index]._index = index

    @make_thread_safe
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        # this is needed because otherwise this breaks with a negative index,
        # and this code handles indexes like python does it
        index = range(len(self))[index]

        del self[index]
        self.insert(index, value)

    @make_thread_safe
    def __len__(self):
        return len(self._items)

    @make_thread_safe
    def insert(self, index, item: MenuItem):
        if not isinstance(item, MenuItem):
            # TODO: test that tuples are handled correctly here because that
            #       might be a common mistake
            raise TypeError("expected a MenuItem, got %r" % (item,))

        # handle the index line python does it
        item._prepare_adding()
        self._items.insert(index, item)
        index = self._items.index(item)
        self._call(None, self, 'insert', index, item.type)
        item._after_adding(self, index)

        # inserting to self._items messed up items after the index
        for index2 in range(index + 1, len(self._items)):
            self._items[index2]._index = index2

    def popup(self, x, y, menu_item=None):
        """Displays the menu on the screen.

        x and y are coordinates in pixels, relative to the screen. See
        :man:`tk_popup(3tk)` for details. If *menu_item* is given, its index
        is passed to :man:`tk_popup(3tk)`.

        There are two ways to show popup menus in Tk. This is one of them, and
        ``post`` is another. I spent a while trying to find something that
        explains the difference, and the best thing I found is `this book <htt\
ps://books.google.fi/books?id=BWf6mdwHjDMC&printsec=frontcover&hl=fi#v=onepage\
&q&f=false>`_. The book uses ``tk_popup``, and one of the authors is John
        Ousterhout, the creator of Tcl and Tk.
        """
        if menu_item is None:
            tk.tcl_call(None, 'tk_popup', self, x, y)
        else:
            menu_item._check_in_menu()
            tk.tcl_call(None, 'tk_popup', self, x, y, menu_item._index)
