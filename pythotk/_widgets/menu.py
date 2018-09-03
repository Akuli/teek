import collections.abc

import pythotk as tk
from pythotk._structures import CgetConfigureConfigDict
from pythotk._tcl_calls import needs_main_thread
from pythotk._widgets.base import Widget


# instances of this class assume that the indexes don't change unexpectedly
# TODO: document that
class MenuItem:

    def __init__(self, menu, index):
        self._menu = menu
        self._index = index

        # this line of code feels like java
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
        return '<%s menu item, label=%r>' % (self.type, self.config['label'])

    def _config_entrycommand_caller(self, returntype, subcommand, *args):
        assert subcommand in {'cget', 'configure'}
        return tk.tcl_call(returntype, self._menu, 'entry' + subcommand,
                           self._index, *args)

    def _create_command(self):
        # because there may be multiple MenuItem objects that represent the
        # same item index
        existing_command_string = tk.tcl_call(str, self._menu, 'entrycget',
                                              self._index, '-command')
        try:
            return self._menu._command_callback_cache[existing_command_string]
        except KeyError:
            pass

        result = tk.Callback()
        command_string = tk.create_command(result.run)
        self._menu._command_callback_cache[command_string] = result
        tk.tcl_call(None, self._menu, 'entryconfigure', self._index,
                    '-command', command_string)
        return result

    def __eq__(self, other):
        if not isinstance(other, MenuItem):
            return NotImplemented
        return self._menu is other._menu and self._index == other._index

    def __hash__(self):
        return hash((self._menu, self._index))

    @property
    def type(self):
        """A string like ``'command'`` or ``'separator'``.

        See ``pathName type`` in :man:`menu(3tk)` for details.
        """
        return tk.tcl_call(str, self._menu, 'type', self._index)


# does not use ChildMixin because usually it's a bad idea to e.g. pack a menu
class Menu(Widget, collections.abc.MutableSequence):
    """A menu widget that can be e.g. added to a :class:`.Window`."""

    def __init__(self, items=(), **kwargs):
        kwargs.setdefault('tearoff', False)
        super().__init__('menu', None, **kwargs)

        # keys are string values of -command, values are Callbacks
        self._command_callback_cache = {}

        self.extend(items)

    def destroy(self):
        super().destroy()
        for command in self._command_callback_cache:
            tk.delete_command(command)
        self._command_callback_cache.clear()    # because why not

    def _repr_parts(self):
        return ['contains %d items' % len(self)]

    @needs_main_thread
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        index = range(len(self))[index]    # handle indexes like python does it
        return MenuItem(self, index)

    @needs_main_thread
    def __delitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        index = range(len(self))[index]
        self._call(None, self, 'delete', index)

    @needs_main_thread
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise TypeError("slicing a Menu widget is not supported")

        # FIXME: this breaks with a negative index
        del self[index]
        self.insert(index, value)

    def __len__(self):
        # '$widget index end' returns the last index, not the total number of
        # items
        length = self._call(str, self, 'index', 'end')
        if length == 'none':    # no items
            return 0
        return int(length) + 1

    def insert(self, index, item):
        if item and isinstance(item[-1], collections.abc.Mapping):
            options = item[-1]
            item = item[:-1]
        else:
            options = {}

        do_after_adding = lambda menuitem: None     # noqa

        if not item:
            type_ = 'separator'
        elif len(item) == 2:
            options['label'], second_object = item
            if isinstance(second_object, tk.BooleanVar):
                type_ = 'checkbutton'
                options['variable'] = second_object
            elif callable(second_object):
                type_ = 'command'
                do_after_adding = lambda menuitem: (
                    menuitem.config['command'].connect(second_object))
            elif isinstance(second_object, Menu):
                type_ = 'cascade'
                options['menu'] = second_object
            else:   # assume an iterable
                type_ = 'cascade'
                options['menu'] = Menu(second_object)
        elif len(item) == 3:
            type_ = 'radiobutton'
            options['label'], options['variable'], options['value'] = item
        else:
            raise TypeError(
                "expected a sequence of length 0, 2 or 3, got " + repr(item))

        # lists do this
        if index < 0:
            index += len(self)
        if index < 0:
            index = 0
        if index > len(self):
            index = len(self)

        args = []
        for option, value in options.items():
            args.extend(['-' + option, value])

        self._call(None, self, 'insert', index, type_, *args)
        do_after_adding(self[index])
