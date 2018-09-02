import pythotk as tk
from pythotk._tcl_calls import from_tcl, needs_main_thread
from pythotk._widgets.base import Widget, ChildMixin


class Button(ChildMixin, Widget):
    """A widget that runs a callback when it's clicked.

    ``text`` can be given as with :class:`Label`.

    The ``'command'`` option is not settable, and its value is a
    :class:`.Callback` that runs with no arguments when the button is
    clicked. If the *command* argument is given, it will be treated so that
    this...
    ::

        button = tk.Button(some_widget, "Click me", do_something)

    ...does the same thing as this::

        button = tk.Button(some_widget, "Click me")
        button.config['command'].connect(do_something)

    See :meth:`.Callback.connect` documentation if you need to pass arguments
    to the ``do_something`` function.

    Manual page: :man:`ttk_button(3tk)`
    """

    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__('ttk::button', parent, text=text, **kwargs)
        self.config._types.update({
            'default': str,
        })
        self.config._special['command'] = self._create_click_command

        if command is not None:
            self.config['command'].connect(command)

    def _create_click_command(self):
        result = tk.Callback()
        command_string = tk.create_command(result.run)
        self._command_list.append(command_string)
        self._call(None, self, 'configure', '-command', command_string)
        return result

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]

    def invoke(self):
        """Runs the command callback.

        See ``pathname invoke`` in :man:`ttk_button(3tk)` for details.
        """
        self._call(None, self, 'invoke')


class Checkbutton(ChildMixin, Widget):
    """A square-shaped, checkable box with text next to it.

    For convenience, ``text`` and ``command`` arguments work the same way as
    with :class:`.Button`.

    The ``'command'`` option is not settable, and its value is a
    :class:`.Callback`. By default, it runs with ``True`` as the only argument
    when the checkbutton is checked, and with ``False`` when the checkbutton is
    unchecked. You can pass ``onvalue=False, offvalue=True`` to reverse this if
    you find it useful for some reason. This also affects the values that end
    up in the ``'variable'`` option (see manual page), which is a
    :class:`.BooleanVar`.

    Example::

        import pythotk as tk

        def on_check_or_uncheck(checked):
            if checked:
                print("Checked")
            else:
                print("Unchecked")

        window = tk.Window("Checkbutton Example")
        tk.Checkbutton(window, "Check me", on_check_or_uncheck).pack()
        tk.run()

    Manual page: :man:`ttk_checkbutton(3tk)`
    """

    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__('ttk::checkbutton', parent, text=text, **kwargs)
        self.config._types.update({
            'onvalue': bool,
            'offvalue': bool,
            'variable': tk.BooleanVar,
        })
        self.config._special['command'] = self._create_check_command

        if command is not None:
            self.config['command'].connect(command)

    def _command_runner(self):
        self.config['command'].run(self.config['variable'].get())

    def _create_check_command(self):
        result = tk.Callback()
        command_string = tk.create_command(self._command_runner)
        self._command_list.append(command_string)
        self._call(None, self, 'configure', '-command', command_string)
        return result

    def invoke(self):
        """
        Checks or unchecks the checkbutton, updates the variable and runs the
        command callback.

        See ``pathname invoke`` in :man:`ttk_checkbutton(3tk)` for details.
        """
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


class Frame(ChildMixin, Widget):
    """An empty widget. Frames are often used as containers for other widgets.

    Manual page: :man:`ttk_frame(3tk)`
    """

    def __init__(self, parent, **options):
        super().__init__('ttk::frame', parent, **options)
        self.config._types.update({
            'padding': tk.ScreenDistance,
        })


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


class LabelFrame(ChildMixin, Widget):
    """A frame with a visible border line and title text.

    For convenience, the ``text`` option can be given as with :class:`.Label`.

    Manual page: :man:`ttk_labelframe(3tk)`
    """

    def __init__(self, parent, text='', **kwargs):
        super().__init__('ttk::labelframe', parent, text=text, **kwargs)
        self.config._types.update({
            'labelanchor': str,
            'labelwidget': Widget,
        })

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]


class Scrollbar(ChildMixin, Widget):
    """A widget for scrolling other widgets, like :class:`.Text`.

    In order to use a scrollbar, there are two things you need to do:

    1. Tell a scrollable widget (e.g. :class:`.Text`) to use the scrollbar.
    2. Tell the scrollbar to scroll the widget.

    For example::

        import pythotk as tk

        window = tk.Window()

        text = tk.Text(window)
        text.pack(side='left', fill='both', expand=True)
        scrollbar = tk.Scrollbar(window)
        scrollbar.pack(side='left', fill='y')

        text.config['yscrollcommand'].connect(scrollbar.set)  # 1.
        scrollbar.config['command'].connect(text.yview)       # 2.

        tk.run()

    The value of the scrollbar's ``'command'`` option is a :class:`.Callback`
    that runs when the scrollbar is scrolled. It runs with arguments suitable
    for :meth:`.Text.xview` or :meth:`.Text.yview`. See ``SCROLLING COMMANDS``
    in :man:`ttk_scrollbar(3tk)` for details about the arguments.

    Manual page: :man:`ttk_scrollbar(3tk)`
    """

    def __init__(self, parent, **kwargs):
        super().__init__('ttk::scrollbar', parent, **kwargs)
        self.config._special['command'] = self._create_scrolling_command

    # this runs when the user moves the scrollbar
    def _command_runner(self, *args):
        if args[0] == 'moveto':
            moveto, fraction = args
            fraction = from_tcl(float, fraction)
            self.config['command'].run('moveto', fraction)
        elif args[0] == 'scroll' and args[-1] in ('units', 'pages'):
            scroll, number, units_or_pages = args
            number = from_tcl(int, number)
            self.config['command'].run('scroll', number, units_or_pages)
        else:   # pragma: no cover
            raise ValueError("ttk::scrollbar's command ran with unexpected "
                             "arguments: " + repr(args))

    def _create_scrolling_command(self):
        result = tk.Callback()
        command_string = tk.create_command(
            self._command_runner, extra_args_type=str)
        self._command_list.append(command_string)
        self._call(None, self, 'configure', '-command', command_string)
        return result

    def set(self, first, last):
        """Set the scrollbar's position.

        See ``pathName set`` in :man:`ttk_scrollbar(3tk)` for details.
        """
        self._call(None, self, 'set', first, last)

    def get(self):
        """Return a two-tuple of floats that have been passed to :meth:`set`.

        See also ``pathName get`` in :man:`ttk_scrollbar(3tk)`.
        """
        return self._call((float, float), self, 'get')


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

    def _repr_parts(self):
        return ['orient=' + repr(self.config['orient'])]
