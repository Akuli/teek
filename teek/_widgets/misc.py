import teek
from teek._tcl_calls import from_tcl, make_thread_safe
from teek._widgets.base import Widget, ChildMixin


class Button(ChildMixin, Widget):
    """A widget that runs a callback when it's clicked.

    See :source:`examples/button.py` for example code.

    ``text`` can be given as with :class:`Label`. The ``'command'`` option is
    not settable, and its value is a :class:`.Callback` that runs with no
    arguments when the button is clicked. If the *command* argument is given,
    it will be treated so that this...
    ::

        button = teek.Button(some_widget, "Click me", do_something)

    ...does the same thing as this::

        button = teek.Button(some_widget, "Click me")
        button.config['command'].connect(do_something)

    See :meth:`.Callback.connect` documentation if you need to pass arguments
    to the ``do_something`` function.

    Manual page: :man:`ttk_button(3tk)`
    """

    _widget_name = 'ttk::button'
    tk_class_name = 'TButton'

    @make_thread_safe
    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        if command is not None:
            self.config['command'].connect(command)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'default': str,
            'width': teek.ScreenDistance,
        })
        self.config._special['command'] = self._create_click_command

    def _create_click_command(self):
        result = teek.Callback()
        command_string = teek.create_command(result.run)
        self.command_list.append(command_string)
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

    See :source:`examples/checkbutton.py` for example code.

    For convenience, ``text`` and ``command`` arguments work the same way as
    with :class:`.Button`.

    The ``'command'`` option is not settable, and its value is a
    :class:`.Callback`. By default, it runs with ``True`` as the only argument
    when the checkbutton is checked, and with ``False`` when the checkbutton is
    unchecked. You can pass ``onvalue=False, offvalue=True`` to reverse this if
    you find it useful for some reason. This also affects the values that end
    up in the ``'variable'`` option (see manual page), which is a
    :class:`.BooleanVar`.

    Manual page: :man:`ttk_checkbutton(3tk)`
    """

    _widget_name = 'ttk::checkbutton'
    tk_class_name = 'TCheckbutton'

    @make_thread_safe
    def __init__(self, parent, text='', command=None, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        if command is not None:
            self.config['command'].connect(command)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'onvalue': bool,
            'offvalue': bool,
            'variable': teek.BooleanVar,
            'width': teek.ScreenDistance,
        })
        self.config._special['command'] = self._create_check_command

    def _command_runner(self):
        self.config['command'].run(self.config['variable'].get())

    def _create_check_command(self):
        result = teek.Callback()
        command_string = teek.create_command(self._command_runner)
        self.command_list.append(command_string)
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

    _widget_name = 'ttk::entry'
    tk_class_name = 'TEntry'

    @make_thread_safe
    def __init__(self, parent, text='', **kwargs):
        super().__init__(parent, **kwargs)
        self._call(None, self, 'insert', 0, text)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'exportselection': bool,
            #invalidcommand: ???,
            'show': str,
            'validate': str,
            #'validatecommand': ???,
            'width': int,       # NOT a screen distance
        })

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
    @make_thread_safe
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


class Spinbox(Entry):
    """An entry with up and down buttons.

    This class inherits from :class:`.Entry`, so it has all the attributes and
    methods of :class:`.Entry`, like :attr:`~.Entry.text` and
    :attr:`~.Entry.cursor_pos`.

    The value of the ``'command'`` option is a :class:`.Callback` that is ran
    with no arguments. If a ``command`` keyword argument is given, it will be
    connected to the callback automatically.

    Manual page: :man:`ttk_spinbox(3tk)`
    """

    _widget_name = 'ttk::spinbox'
    tk_class_name = 'TSpinbox'

    @make_thread_safe
    def __init__(self, parent, *, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        if command is not None:
            self.config['command'].connect(command)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'from': float,
            'to': float,
            'increment': float,
            'values': [str],
            'wrap': bool,
            'format': str,
        })
        self.config._special['command'] = self._create_spin_command

    def _create_spin_command(self):
        result = teek.Callback()
        command_string = teek.create_command(result.run)
        self.command_list.append(command_string)
        self._call(None, self, 'configure', '-command', command_string)
        return result


class Combobox(Entry):
    """An entry that displays a list of valid values.

    This class inherits from :class:`.Entry`, so it has all the attributes and
    methods of :class:`.Entry`, like :attr:`~.Entry.text` and
    :attr:`~.Entry.cursor_pos`.

    Manual page: :man:`ttk_combobox(3tk)`
    """

    _widget_name = 'ttk::combobox'
    tk_class_name = 'TCombobox'

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'height': int,
            'values': [str],
        })


class Frame(ChildMixin, Widget):
    """An empty widget. Frames are often used as containers for other widgets.

    Manual page: :man:`ttk_frame(3tk)`
    """

    _widget_name = 'ttk::frame'
    tk_class_name = 'TFrame'

    def _init_config(self):
        super()._init_config()

        # if you change these, also change Window's types in windows.py
        self.config._types.update({
            'height': teek.ScreenDistance,
            'padding': teek.ScreenDistance,
            'width': teek.ScreenDistance,
        })


class Label(ChildMixin, Widget):
    """A widget that displays text.

    For convenience, the ``text`` option can be also given as a positional
    initialization argument, so ``teek.Label(parent, "hello")`` and
    ``teek.Label(parent, text="hello")`` do the same thing.

    Manual page: :man:`ttk_label(3tk)`
    """

    _widget_name = 'ttk::label'
    tk_class_name = 'TLabel'

    def __init__(self, parent, text='', **kwargs):
        super().__init__(parent, text=text, **kwargs)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'width': teek.ScreenDistance,
        })

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]


class LabelFrame(ChildMixin, Widget):
    """A frame with a visible border line and title text.

    For convenience, the ``text`` option can be given as with :class:`.Label`.

    Manual page: :man:`ttk_labelframe(3tk)`
    """

    _widget_name = 'ttk::labelframe'
    tk_class_name = 'TLabelframe'

    def __init__(self, parent, text='', **kwargs):
        super().__init__(parent, text=text, **kwargs)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'height': teek.ScreenDistance,
            'labelanchor': str,
            'labelwidget': Widget,
            'width': teek.ScreenDistance,
        })

    def _repr_parts(self):
        return ['text=' + repr(self.config['text'])]


class Progressbar(ChildMixin, Widget):
    """
    Displays progress of a long-running operation. This is useful if you are
    :ref:`running something concurrently <concurrency>` and you want to let the
    user know that something is happening.

    The progress bar can be used in two modes. Pass ``mode='indeterminate'``
    and call :meth:`start` to make the progress bar bounce back and forth
    forever. If you want to create a progress bar that actually displays
    progress instead of just letting the user know that something is happening,
    don't pass ``mode='indeterminate'``; the default is ``mode='determinate'``,
    which does what you want.

    There's a ``'value'`` option that can be used to set the progress in
    determinate mode. A value of 0 means that nothing is done, and 100 means
    that we are ready. If you do math on a regular basis, that's all you need
    to know, but if you are not very good at math, keep reading:

    .. admonition:: Progress Math

        If your program does 5 things, and 2 of them are done, you should do
        this::

            progress_bar.config['value'] = (2 / 5) * 100

        It works like this:

        * The program has done 2 things out of 5; that is, 2/5. That is a
          division. Its value turns out to be 0.4.
        * We want percents. They are numbers between 0 and 100. The
          ``done / total`` calculation gives us a number between 0 and 1; if we
          have done nothing, we have ``0 / 5 == 0.0``, and if we have done
          everything, we have ``5 / 5 == 1.0``. If we add ``* 100``, we get
          ``0.0 * 100 = 0.0`` when we haven't done anything, and
          ``1.0 * 100 == 100.0`` when we have done everything. Awesome!

        ::

            progress_bar.config['value'] = (done / total) * 100

        However, this fails if ``total == 0``:

        >>> 1/0
        Traceback (most recent call last):
            ...
        ZeroDivisionError: division by zero

        If we have no work to do and we have done nothing (``0/0``), then how
        many percents of the work is done? It doesn't make sense. You can
        handle these cases e.g. like this::

            if total == 0:
                # 0/0 things done, make the progress bar grayed out because
                # there is no progress to indicate
                progress_bar.state.add('disabled')
            else:
                progress_bar.config['value'] = (done / total) * 100

    If multiplying by 100 is annoying, you can create the progress bar like
    this...
    ::

        progress_bar = teek.Progressbar(parent_widget, maximum=1)

    ...and then set numbers between 0 and 1 to
    ``progress_bar.config['value']``::

        if total == 0:
            progress_bar.state.add('disabled')
        else:
            progress_bar.config['value'] = done / total

    Manual page: :man:`ttk_progressbar(3tk)`
    """

    _widget_name = 'ttk::progressbar'
    tk_class_name = 'TProgressbar'

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'orient': str,
            'length': teek.ScreenDistance,    # undocumented but true
            'maximum': float,
            'mode': str,
            #'phase': ???,
            'value': float,
            'variable': teek.FloatVar,
        })

    def _repr_parts(self):
        result = ['mode=' + repr(self.config['mode'])]
        if self.config['mode'] == 'determinate':
            result.append('value=' + repr(self.config['value']))
            result.append('maximum=' + repr(self.config['maximum']))
        return result

    def start(self, interval=50):
        """Makes an indeterminate mode progress bar bounce back and forth.

        The progress bar will move by a tiny bit every *interval* milliseconds.
        A small interval makes the progress bar look smoother, but don't make
        it too small to avoid keeping CPU usage down. The default should be
        good enough for most things.
        """
        self._call(None, self, 'start', interval)

    def stop(self):
        """Stops the bouncing started by :meth:`start`."""
        self._call(None, self, 'stop')


class Scrollbar(ChildMixin, Widget):
    """A widget for scrolling other widgets, like :class:`.Text`.

    In order to use a scrollbar, there are two things you need to do:

    1. Tell a scrollable widget (e.g. :class:`.Text`) to use the scrollbar.
    2. Tell the scrollbar to scroll the widget.

    For example::

        import teek

        window = teek.Window()

        text = teek.Text(window)
        text.pack(side='left', fill='both', expand=True)
        scrollbar = teek.Scrollbar(window)
        scrollbar.pack(side='left', fill='y')

        text.config['yscrollcommand'].connect(scrollbar.set)  # 1.
        scrollbar.config['command'].connect(text.yview)       # 2.

        window.on_delete_window.connect(teek.quit)
        teek.run()

    The value of the scrollbar's ``'command'`` option is a :class:`.Callback`
    that runs when the scrollbar is scrolled. It runs with arguments suitable
    for :meth:`.Text.xview` or :meth:`.Text.yview`. See ``SCROLLING COMMANDS``
    in :man:`ttk_scrollbar(3tk)` for details about the arguments.

    Manual page: :man:`ttk_scrollbar(3tk)`
    """

    _widget_name = 'ttk::scrollbar'
    tk_class_name = 'TScrollbar'

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
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
        result = teek.Callback()
        command_string = teek.create_command(
            self._command_runner, extra_args_type=str)
        self.command_list.append(command_string)
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

        separator = teek.Separator(some_widget, orient='horizontal')
        separator.pack(fill='x')    # default is side='top'

    ...and create a vertical separator like this::

        separator = teek.Separator(some_widget, orient='vertical')
        separator.pack(fill='y', side='left')   # can also use side='right'

    See :source:`examples/separator.py` for more example code.

    Manual page: :man:`ttk_separator(3tk)`
    """
    # TODO: link to pack docs

    _widget_name = 'ttk::separator'
    tk_class_name = 'TSeparator'

    def _repr_parts(self):
        return ['orient=' + repr(self.config['orient'])]
