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
            args.append('-' + name)
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
        self.config._special_options['title'] = (
            lambda title: tkinder.tk.call('wm', 'title', self.path, title),
            lambda: tkinder.tk.call('wm', 'title', self.path),
        )
        self.config.title = title
        self.on_close = structures.Callback()
        tkinder.tk.call('wm', 'protocol', self.path, 'WM_DELETE_WINDOW',
                        _mainloop.create_command(self.on_close.run))

    def _repr_parts(self):
        return ['title=' + repr(self.config.title)]


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

        self.config._special_options['command'] = (
            self._command_error, self._command_error)

    def _command_error(self, junk=None):
        # Callback catches TclError so we'll raise it here
        raise _tkinter.TclError("the 'command' option is not supported, "
                                "use the on_click callback instead")

    def _repr_parts(self):
        return ['text=' + repr(self.config.text)]
