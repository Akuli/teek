import collections.abc

import pythotk as tk
from pythotk._structures import CgetConfigureConfigDict
from pythotk._tcl_calls import needs_main_thread
from pythotk._widgets.base import Widget


# all menu item things that do something run in the main thread to avoid any
# kind of use of menu items that are in an inconsistent state, and the Menu
# class also does this... think of it as poor man's locking or something
class MenuItem:

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

    @needs_main_thread
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
        self._menu._command_list.append(command_string)
        return result


# does not use ChildMixin because usually it's a bad idea to e.g. pack a menu
# TODO: document that this class assumes that nothing else changes the
#       underlying Tcl widget
class Menu(Widget, collections.abc.MutableSequence):
    """A menu widget that can be e.g. added to a :class:`.Window`."""

    def __init__(self, items=(), **kwargs):
        kwargs.setdefault('tearoff', False)
        super().__init__('menu', None, **kwargs)
        self._items = []
        self.extend(items)

    def _repr_parts(self):
        return ['contains %d items' % len(self)]

    @needs_main_thread
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")
        return self._items[index]

    @needs_main_thread
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

    @needs_main_thread
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        # this is needed because otherwise this breaks with a negative index,
        # and this code handles indexes like python does it
        index = range(len(self))[index]

        del self[index]
        self.insert(index, value)

    @needs_main_thread
    def __len__(self):
        return len(self._items)

    @needs_main_thread
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
