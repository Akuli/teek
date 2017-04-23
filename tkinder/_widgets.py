import collections.abc as abcoll
import _tkinter

import tkinder
from tkinder import _mainloop, structures

_widgets = {}
_mainloop.on_quit.connect(_widgets.clear)


class Widget:
    """A base class for all widgets."""

    @_mainloop.requires_init
    def __init__(self, widgetname, parent=None, **kwargs):
        if parent is None:
            parentpath = ''
        else:
            parentpath = parent.path
        self.parent = parent

        counter = _mainloop.counts[widgetname]
        self.path = parentpath + '.' + widgetname + str(next(counter))
        tkinder.tk.call(widgetname, self.path)
        _widgets[self.path] = self

        self.config = structures._Config(self)
        if kwargs:
            self.config(**kwargs)

    def __repr__(self):
        if self.destroyed:
            # _repr_parts() doesn't need to work with destroyed widgets
            prefix = 'destroyed ' + self._repr_prefix()
            parts = None
        else:
            prefix = self._repr_prefix()
            parts = self._repr_parts()

        if parts is None:
            return '<{} at 0x{:x}>'.format(prefix, id(self))
        return '<' + ', '.join([prefix] + parts) + '>'

    @classmethod
    def _repr_prefix(cls):
        if cls.__module__ == '__name__':
            # we don't set __module__ to 'tkinder' because it screws up
            # inspect.getsource
            return 'tkinder.' + cls.__name__
        return cls.__module__ + '.' + cls.__name__

    def _repr_parts(self):
        # overrided in subclasses
        return None

    def destroy(self):
        """Delete this widget and all child widgets."""
        for child in tkinder.tk.call('winfo', 'children', self.path):
            _widgets[child].destroy()
        tkinder.tk.call('destroy', self.path)
        del _widgets[self.path]

    @property
    def destroyed(self):
        """Check if :meth:`~destroy` has been called."""
        # can't just check if self.path is in the widget dict because
        # another widget with the same path might exist
        return (_widgets.get(self.path, None) is not self)


class ChildMixin:

    def pack(self, **kwargs):
        args = ['pack', self.path]
        for name, value in kwargs.items():
            if isinstance(value, Widget):
                value = value.path
            args.append('-' + name.rstrip('_'))
            args.append(value)
        tkinder.tk.call(*args)

    def pack_forget(self):
        tkinder.tk.call('pack', 'forget', self.path)

    def pack_info(self):
        stupid_tk_dict = tkinder.tk.call('pack', 'info', self.path)
        result = {}

        # loop over it in pairs
        iterator = iter(tkinder.tk.splitlist(stupid_tk_dict))
        for option, value in zip(iterator, iterator):
            result[option.lstrip('-')] = value

        result['in'] = _widgets[str(result['in'])]
        return result


class Window(Widget):

    def __init__(self, title="Tkinder Window", **kwargs):
        super().__init__('toplevel', **kwargs)
        self.title = title
        self.on_close = structures.Callback()
        tkinder.tk.call('wm', 'protocol', self.path, 'WM_DELETE_WINDOW',
                        _mainloop.create_command(self.on_close.run))

    def _repr_parts(self):
        return ['title=' + repr(self.title)]

    @property
    def title(self):
        return tkinder.tk.call('wm', 'title', self.path)

    @title.setter
    def title(self, new_title):
        tkinder.tk.call('wm', 'title', self.path, new_title)


class Frame(ChildMixin, Widget):

    def __init__(self, **kwargs):
        super().__init__('frame', **kwargs)


class Label(ChildMixin, Widget):

    def __init__(self, parent, text='', **kwargs):
        super().__init__('label', parent, text=text, **kwargs)

    def _repr_parts(self):
        return ['text=' + repr(self.config.text)]


class Button(ChildMixin, Widget):

    def __init__(self, parent, text='', *, command=None, **kwargs):
        super().__init__('button', parent, text=text, **kwargs)
        self.on_click = structures.Callback()
        self.config.command = _mainloop.create_command(self.on_click.run)
        if command is not None:
            self.on_click.connect(command)
        self.config._disabled['command'] = "the on_click callback"

    def _repr_parts(self):
        return ['text=' + repr(self.config.text)]


class _SelectedIndexesView(abcoll.MutableSet):
    """A set-like view of currently selected indexes.

    Negative and out-of-range indexes are not allowed.
    """

    def __init__(self, listbox):
        self._listbox = listbox

    def __repr__(self):
        return '<Listbox selected_indexes view: %s>' % repr(set(self))

    def __iter__(self):
        return iter(tkinder.tk.call(self._listbox.path, 'curselection'))

    def __len__(self):
        return len(tkinder.tk.call(self._listbox.path, 'curselection'))

    def __contains__(self, index):
        return bool(tkinder.tk.call(
            self._listbox.path, 'selection', 'includes', index))

    def add(self, index):
        """Select an index in the listbox if it's not currently selected."""
        if index not in range(len(self._listbox)):
            raise ValueError("listbox index %r out of range" % (index,))
        tkinder.tk.call(self._listbox.path, 'selection', 'set', index)

    def discard(self, index):
        """Unselect an index in the listbox if it's currently selected."""
        if index not in range(len(self._listbox)):
            raise ValueError("listbox index %r out of range" % (index,))
        tkinder.tk.call(self._listbox.path, 'selection', 'clear', index)

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
        return tkinder.tk.call(self.path, 'index', 'end')

    def _fix_index(self, index):
        if index < 0:
            index += len(self)
        if index not in range(len(self)):
            raise IndexError("listbox index %d out of range" % index)
        return index

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        return tkinder.tk.call(self.path, 'get', self._fix_index(index))

    def __delitem__(self, index):
        if isinstance(index, slice):
            # these need to be deleted in reverse because deleting
            # something changes all indexes after it
            indexes = list(range(*index.indices(len(self))))
            indexes.sort(reverse=True)
            for i in indexes:
                del self[i]

        tkinder.tk.call(self.path, 'delete', self._fix_index(index))

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
        tkinder.tk.call(self.path, 'insert', index, item)
