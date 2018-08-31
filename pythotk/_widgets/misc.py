from pythotk._font import Font
from pythotk._structures import Callback, ScreenDistance
from pythotk._tcl_calls import create_command, needs_main_thread
from pythotk._widgets.base import Widget, ChildMixin


class Frame(ChildMixin, Widget):
    """An empty widget. Frames are often used as containers for other widgets.

    Manual page: :man:`ttk_frame(3tk)`
    """

    def __init__(self, parent, **options):
        super().__init__('ttk::frame', parent, **options)
        self.config._types.update({
            'padding': ScreenDistance,
        })


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

        # TODO: fill in other types
        self.config._types.update({
            'font': Font,
        })

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

    See :meth:`.Callback.connect` if you need to pass arguments to the
    ``do_something`` function.

    Manual page: :man:`ttk_button(3tk)`

    .. attribute:: on_click

        A :class:`Callback` that runs when the button is clicked.
    """

    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__('ttk::button', parent, text=text, **kwargs)
        self.config._types.update({
            'default': str,
        })

        self.on_click = Callback()
        command_string = create_command(self.on_click.run)
        self._command_list.append(command_string)
        self.config['command'] = command_string
        self.config._disabled['command'] = ("use the on_click attribute " +
                                            "or an initialization argument")
        if command is not None:
            self.on_click.connect(command)

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]

    def invoke(self):
        self._call(None, self, 'invoke')


class Entry(ChildMixin, Widget):
    """A widget for asking the user to enter a one-line string.

    The ``text`` option works as with :class:`.Label`.

    .. seealso::
        Use :class:`.Label` if you want to display text without letting the
        user edit it. Entries are also not suitable for text with more than
        one line; use :class:`.Text` instead if you want multiple lines.

    Manual page: :man:`ttk_entry(3tk)`
    """

    def __init__(self, parent, text='', **kwargs):
        super().__init__('ttk::entry', parent, **kwargs)
        self.config._types.update({
            #invalidcommand: ???,
            'show': str,
            'validate': str,
            #'validatecommand': ???,
            'width': int,       # NOT a screen distance
        })
        self._call(None, self, 'insert', 0, text)

        self.config._types['exportselection'] = bool
        # TODO: textvariable should be a StringVar

    def _repr_parts(self):
        return ['text=' + repr(self.text)]

    @property
    def text(self):
        """The string of text in the entry widget.

        Setting and getting this attribute calls ``get``, ``insert`` and
        ``delete`` documented in :man:`ttk_entry(3tk)`.
        """
        return self._call(str, self, 'get')

    @text.setter
    @needs_main_thread
    def text(self, new_text):
        self._call(None, self, 'delete', 0, 'end')
        self._call(None, self, 'insert', 0, new_text)

    @property
    def cursor_pos(self):
        """
        The integer index of the cursor in the entry, so that
        ``entry.text[:entry.cursor_pos]`` and ``entry.text[entry.cursor_pos:]``
        are the text before and after the cursor, respectively.

        You can set this attribute to move the cursor.
        """
        return self._call(int, self, 'index', 'insert')

    @cursor_pos.setter
    def cursor_pos(self, new_pos):
        self._call(None, self, 'icursor', new_pos)
