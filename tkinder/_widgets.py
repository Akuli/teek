import keyword
import _tkinter

from . import _mainloop, structures


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
        _mainloop.tk.call(widgetname, self.path)

        self.config = structures._Config(self)
        if kwargs:
            self.config(**kwargs)

    def __repr__(self):
        module = type(self).__module__
        if module == __name__:
            # this doesn't set __module__ to 'tkinder' because it screws
            # up inspect.getsource
            module = 'tkinder'

        prefix = '%s.%s widget' % (module, type(self).__name__)
        parts = self._repr_parts()
        if parts is None:
            return '<{} at 0x{:x}>'.format(prefix, id(self))
        return '<' + ', '.join([prefix] + parts) + '>'

    def _repr_parts(self):
        return None

    def destroy(self):
        print("destroying")
        # TODO: destroy child widgets too
        _mainloop.tk.call('destroy', self.path)


def _pairs(iterable):
    """Return an iterator of pairs from an iterable.

    >>> list(_pairs(['a', 'b', 'c', 'd']))
    [('a', 'b'), ('c', 'd')]
    """
    iterator = iter(iterable)
    return zip(iterator, iterator)


class ChildMixin:

    def pack(self, **kwargs):
        args = ['pack', self.path]
        for name, value in kwargs.items():
            args.append('-' + name)
            args.append(value)
        _mainloop.tk.call(*args)

    def pack_forget(self):
        _mainloop.tk.call('pack', 'forget', self.path)

    def pack_info(self):
        stupid_tk_dict = _mainloop.tk.call('pack', 'info', self.path)
        result = {}
        for option, value in _pairs(_mainloop.tk.splitlist(stupid_tk_dict)):
            result[option.lstrip('-')] = value
        return result


class Window(Widget):

    # title can be a positional argument
    def __init__(self, title="Tkinder Window", **kwargs):
        super().__init__('toplevel', **kwargs)
        self.config._special_options['title'] = (
            lambda title: _mainloop.tk.call('wm', 'title', self.path, title),
            lambda: _mainloop.tk.call('wm', 'title', self.path),
        )
        self.config.title = title
        _mainloop.tk.call('wm', 'protocol', self.path, 'WM_DELETE_WINDOW',
                          _mainloop.register_callback(self.destroy))

    def _repr_parts(self):
        return ['title=%r' % self.config.title]


class Label(ChildMixin, Widget):

    # text can be a positional argument
    def __init__(self, parent, text='', **kwargs):
        super().__init__('label', parent, text=text, **kwargs)

    def _repr_parts(self):
        return ['text=%r' % self.config.text]
