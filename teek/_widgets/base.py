import collections.abc
import contextlib
import functools
import keyword
import operator
import re

import teek
from teek._tcl_calls import counts, from_tcl, make_thread_safe
from teek._structures import ConfigDict, CgetConfigureConfigDict, after_quit

_widgets = {}
_class_bindings = {}
after_quit.connect(_widgets.clear)
after_quit.connect(_class_bindings.clear)


# like what you would expect to get for combining @classmethod and @property,
# but doesn't do any magic with assigning, only getting
class _ClassProperty:

    def __init__(self, getter):
        assert isinstance(getter.__name__, str)
        self._getter = getter

    def __get__(self, instance_or_none, claas):
        if instance_or_none is None:
            return self._getter(claas)

        attribute = self._getter.__name__
        classname = claas.__name__
        raise AttributeError(
            "the %s attribute must be used like %s.%s, "
            "not like some_%s_instance.%s"
            % (attribute, classname, attribute,
               classname.lower(), attribute))


class StateSet(collections.abc.MutableSet):

    def __init__(self, widget):
        self._widget = widget

    def __repr__(self):
        # yes, this uses [] even though it behaves like a set, that's the best
        # thing i thought of
        return '<state set: %r>' % (list(self),)

    def __iter__(self):
        return iter(self._widget._call([str], self._widget, 'state'))

    def __len__(self):
        return len(self._widget._call([str], self._widget, 'state'))

    def __contains__(self, state):
        return self._widget._call(bool, self._widget, 'instate', state)

    def add(self, state):
        self._widget._call(None, self._widget, 'state', state)

    def discard(self, state):
        self._widget._call(None, self._widget, 'state', '!' + state)


class GridRowOrColumnConfig(ConfigDict):

    def __init__(self, configure_method):
        super().__init__()
        self._types.update({
            'minsize': teek.ScreenDistance,
            'weight': float,
            'uniform': str,
            'pad': teek.ScreenDistance,
        })
        self._configure = configure_method

    def _set(self, option, value):
        self._configure(None, '-' + option, value)

    def _get(self, option):
        return self._configure(self._types.get(option, str), '-' + option)

    def _list_options(self):
        return (key.lstrip('-') for key in self._configure({}).keys())


class GridRowOrColumn:

    def __init__(self, widget, row_or_column, number):
        super().__init__()
        self._widget = widget
        self._row_or_column = row_or_column
        self._number = number
        self.config = GridRowOrColumnConfig(self._configure)

    def __repr__(self):
        return (
            "<grid %s %d: has a config attribute and a get_slaves() method>"
            % (self._row_or_column, self._number))

    def __eq__(self, other):
        if not isinstance(other, GridRowOrColumn):
            return NotImplemented
        return (self._widget == other._widget and
                self._row_or_column == other._row_or_column and
                self._number == other._number)

    def __hash__(self):
        return hash((self._widget, self._row_or_column, self._number))

    def _configure(self, returntype, *args):
        return self._widget._call(
            returntype, 'grid', self._row_or_column + 'configure',
            self._widget, self._number, *args)

    def get_slaves(self):
        return self._widget._call(
            [Widget], 'grid', 'slaves', self._widget,
            '-' + self._row_or_column, self._number)


# make things more tkinter-user-friendly
def _tkinter_hint(good, bad):
    def dont_use_this(self, *args, **kwargs):
        raise TypeError("use %s, not %s" % (good, bad))

    return dont_use_this


class Widget:
    """This is a base class for all widgets.

    All widgets inherit from this class, and they have all the attributes
    and methods documented here.

    Don't create instances of ``Widget`` yourself like ``Widget(...)``; use one
    of the classes documented below instead. However, you can use ``Widget``
    with :func:`isinstance`; e.g. ``isinstance(thingy, teek.Widget)`` returns
    ``True`` if ``thingy`` is a teek widget.

    .. attribute:: config

        A dict-like object that represents the widget's options.

        >>> window = teek.Window()
        >>> label = teek.Label(window, text='Hello World')
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
        >>> pprint.pprint(dict(label.config))  # prints everything nicely  \
        # doctest: +ELLIPSIS
        {...,
         'text': 'Even newer text',
         ...}

    .. attribute:: state

        Represents the Ttk state of the widget. The state object behaves like a
        :class:`set` of strings. For example, ``widget.state.add('disabled')``
        makes a widget look like it's grayed out, and
        ``widget.state.remove('disabled')`` undoes that. See ``STATES`` in
        :man:`ttk_intro(3tk)` for more details about states.

        .. note::
            Only Ttk widgets have states, and this attribute is set to None for
            non-Ttk widgets. If you don't know what Ttk is, you should read
            about it in :ref:`the teek tutorial <tcl-tk-tkinter-teek>`.
            Most teek widgets are ttk widgets, but some aren't, and that's
            mentioned in the documentation of those widgets.

    .. attribute:: tk_class_name

        Tk's class name of the widget class, as a string.

        This is a class attribute, but it can be accessed from instances as
        well:

        >>> text = teek.Text(teek.Window())
        >>> text.tk_class_name
        'Text'
        >>> teek.Text.tk_class_name
        'Text'

        Note that Tk's class names are sometimes different from the names of
        Python classes, and this attribute can also be None in some special
        cases.

        >>> teek.Label.tk_class_name
        'TLabel'
        >>> class AsdLabel(teek.Label):
        ...     pass
        ...
        >>> AsdLabel.tk_class_name
        'TLabel'
        >>> print(teek.Window.tk_class_name)
        None
        >>> print(teek.Widget.tk_class_name)
        None

    .. attribute:: command_list

        A list of command strings from :func:`.create_command`.

        Append a command to this if you want the command to be deleted with
        :func:`.delete_command` when the widget is destroyed (with e.g.
        :meth:`.destroy`).
    """

    _widget_name = None
    tk_class_name = None

    @make_thread_safe
    def __init__(self, parent, **kwargs):
        if type(self)._widget_name is None:
            raise TypeError("cannot create instances of %s directly, "
                            "use one of its subclasses instead"
                            % type(self).__name__)
        if parent is None:
            parentpath = ''
        else:
            parentpath = parent.to_tcl()
        self.parent = parent

        # yes, it must be lowercase
        safe_class_name = re.sub(r'\W', '_', type(self).__name__).lower()

        # use some_widget.to_tcl() to access the _widget_path
        self._widget_path = '%s.%s%d' % (
            parentpath, safe_class_name, next(counts[safe_class_name]))

        # TODO: some config options can only be given when the widget is
        # created, add support for them
        self._call(None, type(self)._widget_name, self.to_tcl())
        _widgets[self.to_tcl()] = self

        self.config = CgetConfigureConfigDict(
            lambda returntype, *args: self._call(returntype, self, *args))
        self._init_config()     # subclasses should override this and use super

        # support kwargs like from_=1, because from=1 is invalid syntax
        for invalid_syntax in keyword.kwlist:
            if invalid_syntax + '_' in kwargs:
                kwargs[invalid_syntax] = kwargs.pop(invalid_syntax + '_')

        self.config.update(kwargs)

        # command strings that are deleted when the widget is destroyed
        self.command_list = []

        self.bindings = BindingDict(    # BindingDict is defined below
         lambda returntype, *args: self._call(returntype, 'bind', self, *args),
         self.command_list)
        self.bind = self.bindings._convenience_bind

        if type(self)._widget_name.startswith('ttk::'):
            self.state = StateSet(self)
        else:
            self.state = None

    def _init_config(self):
        # width and height aren't here because they are integers for some
        # widgets and ScreenDistances for others... and sometimes the manual
        # pages don't say which, so i have checked them by hand
        self.config._types.update({
            # ttk_widget(3tk)
            'class': str,
            'cursor': str,
            'style': str,

            # options(3tk)
            'activebackground': teek.Color,
            'activeborderwidth': teek.ScreenDistance,
            'activeforeground': teek.Color,
            'anchor': str,
            'background': teek.Color,
            'bg': teek.Color,
            #'bitmap': ???,
            'borderwidth': teek.ScreenDistance,
            'bd': teek.ScreenDistance,
            'cursor': str,
            'compound': str,
            'disabledforeground': teek.Color,
            'exportselection': bool,
            'font': teek.Font,
            'foreground': teek.Color,
            'fg': teek.Color,
            'highlightbackground': teek.Color,
            'highlightcolor': teek.Color,
            'highlightthickness': str,
            'insertbackground': teek.Color,
            'insertborderwidth': teek.ScreenDistance,
            'insertofftime': int,
            'insertontime': int,
            'insertwidth': teek.ScreenDistance,
            'jump': bool,
            'justify': str,
            'orient': str,
            'padx': teek.ScreenDistance,
            'pady': teek.ScreenDistance,
            'relief': str,
            'repeatdelay': int,
            'repeatinterval': int,
            'selectbackground': teek.Color,
            'selectborderwidth': teek.ScreenDistance,
            'selectforeground': teek.Color,
            'setgrid': bool,
            'text': str,
            'troughcolor': teek.Color,
            'wraplength': teek.ScreenDistance,

            # these options are in both man pages
            'textvariable': teek.StringVar,
            'underline': int,
            'image': teek.Image,
            # 'xscrollcommand' and 'yscrollcommand' are done below
            'takefocus': str,   # this one is harder to do right than you think

            # other stuff that many things seem to have
            'padding': teek.ScreenDistance,
            'state': str,
        })

        for option_name in ('xscrollcommand', 'yscrollcommand'):
            self.config._special[option_name] = functools.partial(
                self._create_scroll_callback, option_name)

    @classmethod
    @make_thread_safe
    def from_tcl(cls, path_string):
        """Creates a widget from a Tcl path name.

        In Tcl, widgets are represented as commands, and doing something to the
        widget invokes the command. Use this method if you know the Tcl command
        and you would like to have a widget object instead.

        This method raises :exc:`TypeError` if it's called from a different
        ``Widget`` subclass than what the type of the ``path_string`` widget
        is:

        >>> window = teek.Window()
        >>> teek.Button.from_tcl(teek.Label(window).to_tcl())  \
# doctest: +ELLIPSIS
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

    def __repr__(self):
        class_name = type(self).__name__
        if getattr(teek, class_name, None) is type(self):
            result = 'teek.%s widget' % class_name
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

    def _create_scroll_callback(self, option_name):
        result = teek.Callback()
        command_string = teek.create_command(result.run, [float, float])
        self.command_list.append(command_string)
        self._call(None, self, 'configure', '-' + option_name, command_string)
        return result

    __getitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    __setitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    cget = _tkinter_hint("widget.config['option']", "widget.cget('option')")
    configure = _tkinter_hint("widget.config['option'] = value",
                              "widget.configure(option=value)")

    # like _tcl_calls.tcl_call, but with better error handling
    @make_thread_safe
    def _call(self, *args, **kwargs):
        try:
            return teek.tcl_call(*args, **kwargs)
        except teek.TclError as err:
            if not self.winfo_exists():
                raise RuntimeError("the widget has been destroyed") from None
            raise err

    @make_thread_safe
    def destroy(self):
        """Delete this widget and all child widgets.

        Manual page: :man:`destroy(3tk)`

        .. note::
            Don't override this in a subclass. In some cases, the widget is
            destroyed without a call to this method.

            >>> class BrokenFunnyLabel(teek.Label):
            ...     def destroy(self):
            ...         print("destroying")
            ...         super().destroy()
            ...
            >>> BrokenFunnyLabel(teek.Window()).pack()
            >>> teek.quit()
            >>> # nothing was printed!

            Use the ``<Destroy>`` event instead:

            >>> class WorkingFunnyLabel(teek.Label):
            ...     def __init__(self, *args, **kwargs):
            ...         super().__init__(*args, **kwargs)
            ...         self.bind('<Destroy>', self._destroy_callback)
            ...     def _destroy_callback(self):
            ...         print("destroying")
            ...
            >>> WorkingFunnyLabel(teek.Window()).pack()
            >>> teek.quit()
            destroying
        """
        for name in self._call([str], 'winfo', 'children', self):
            # allow overriding the destroy() method if the widget was
            # created by teek
            if name in _widgets:
                _widgets[name]._destroy_recurser()
            else:
                self._call(None, 'destroy', name)

        # this must be BEFORE deleting command_list commands because <Destroy>
        # bindings may need command_list stuff
        self._call(None, 'destroy', self)

        # this is here because now the widget is basically useless
        del _widgets[self.to_tcl()]

        for command in self.command_list:
            teek.delete_command(command)
        self.command_list.clear()      # why not

    # can be overrided when .destroy() in .destroy() would cause infinite
    # recursion, see Window in windows.py
    def _destroy_recurser(self):
        self.destroy()

    @_ClassProperty
    @make_thread_safe
    def class_bindings(cls):
        if cls is Widget:
            assert cls.tk_class_name is None
            bindtag = 'all'
        elif cls.tk_class_name is not None:
            bindtag = cls.tk_class_name
        else:
            raise AttributeError(
                "%s cannot be used with class_bindings and bind_class()"
                % cls.__name__)

        try:
            return _class_bindings[bindtag]
        except KeyError:
            def call_bind(returntype, *args):
                return teek.tcl_call(returntype, 'bind', bindtag, *args)

            # all commands are deleted when the interpreter shuts down, and the
            # binding dict created here should be alive until then, so it's
            # fine to pass a new empty list for command list
            bindings = BindingDict(call_bind, [])
            _class_bindings[bindtag] = bindings
            return bindings

    @classmethod
    @make_thread_safe
    def bind_class(cls, *args, **kwargs):
        return cls.class_bindings._convenience_bind(*args, **kwargs)

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
        return teek.tcl_call(bool, 'winfo', 'exists', self)

    def winfo_ismapped(self):
        """
        Returns True if the widget is showing on the screen, or False
        otherwise.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(bool, 'winfo', 'ismapped', self)

    def winfo_toplevel(self):
        """Returns the :class:`Toplevel` widget that this widget is in.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(Widget, 'winfo', 'toplevel', self)

    def winfo_width(self):
        """Calls ``winfo width``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'width', self)

    def winfo_height(self):
        """Calls ``winfo height``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'height', self)

    def winfo_reqwidth(self):
        """Calls ``winfo reqwidth``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'reqwidth', self)

    def winfo_reqheight(self):
        """Calls ``winfo reqheight``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'reqheight', self)

    def winfo_x(self):
        """Calls ``winfo x``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'x', self)

    def winfo_y(self):
        """Calls ``winfo y``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'y', self)

    def winfo_rootx(self):
        """Calls ``winfo rootx``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'rootx', self)

    def winfo_rooty(self):
        """Calls ``winfo rooty``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'rooty', self)

    def winfo_id(self):
        """Calls ``winfo id``. Returns an integer.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(int, 'winfo', 'id', self)

    def focus(self, *, force=False):
        """Focuses the widget with :man:`focus(3tk)`.

        If ``force=True`` is given, the ``-force`` option is used.
        """
        if force:
            self._call(None, 'focus', '-force', self)
        else:
            self._call(None, 'focus', self)

    def _geometry_manager_slaves(self, geometry_manager):
        return self._call([Widget], geometry_manager, 'slaves', self)

    pack_slaves = functools.partialmethod(_geometry_manager_slaves, 'pack')
    grid_slaves = functools.partialmethod(_geometry_manager_slaves, 'grid')
    place_slaves = functools.partialmethod(_geometry_manager_slaves, 'place')

    @property
    def grid_rows(self):
        width, height = self._call([int], 'grid', 'size', self)
        return [GridRowOrColumn(self, 'row', number)
                for number in range(height)]

    @property
    def grid_columns(self):
        width, height = self._call([int], 'grid', 'size', self)
        return [GridRowOrColumn(self, 'column', number)
                for number in range(width)]

    grid_rowconfigure = _tkinter_hint(
        "widget.grid_rows[index].config['option'] = value",
        "widget.grid_rowconfigure(index, option=value)")
    grid_columnconfigure = _tkinter_hint(
        "widget.grid_columns[index].config['option'] = value",
        "widget.grid_columnconfigure(index, option=value)")

    def busy_hold(self):
        """See ``tk busy hold`` in :man:`busy(3tk)`.

        *New in Tk 8.6.*
        """
        self._call(None, 'tk', 'busy', 'hold', self)

    def busy_forget(self):
        """See ``tk busy forget`` in :man:`busy(3tk)`.

        *New in Tk 8.6.*
        """
        self._call(None, 'tk', 'busy', 'forget', self)

    def busy_status(self):
        """See ``tk busy status`` in :man:`busy(3tk)`.

        This Returns True or False.

        *New in Tk 8.6.*
        """
        return self._call(bool, 'tk', 'busy', 'status', self)

    @contextlib.contextmanager
    def busy(self):
        """A context manager that calls :func:`busy_hold` and :func:`busy_forg\
et`.

        Example::

            with window.busy():
                # window.busy_hold() has been called, do something
                ...

            # now window.busy_forget() has been called
        """
        self.busy_hold()
        try:
            yield
        finally:
            self.busy_forget()

    def event_generate(self, event, **kwargs):
        """Calls ``event generate`` documented in :man:`event(3tk)`.

        As usual, options are given without dashes as keyword arguments, so Tcl
        code like ``event generate $widget <SomeEvent> -data $theData`` looks
        like ``widget.event_generate('<SomeEvent>', data=the_data)`` in
        teek.
        """
        option_args = []
        for name, value in kwargs.items():
            option_args.extend(['-' + name, value])
        self._call(None, 'event', 'generate', self, event, *option_args)


# these are from bind(3tk), Tk 8.5 and 8.6 support all of these
#
# event(3tk) says that width and height are screen distances, but bind seems to
# convert them to ints, so they are ints here
#
# if you change this, also change docs/bind.rst
_BIND_SUBS = [
    ('%#', int, 'serial'),
    ('%a', int, 'above'),
    ('%b', int, 'button'),
    ('%c', int, 'count'),
    ('%d', str, '_data'),
    ('%f', bool, 'focus'),
    ('%h', int, 'height'),
    ('%i', int, 'i_window'),
    ('%k', int, 'keycode'),
    ('%m', str, 'mode'),
    ('%o', bool, 'override'),
    ('%p', str, 'place'),
    ('%s', str, 'state'),
    ('%t', int, 'time'),
    ('%w', int, 'width'),
    ('%x', int, 'x'),
    ('%y', int, 'y'),
    ('%A', str, 'char'),
    ('%B', int, 'borderwidth'),
    ('%D', int, 'delta'),
    ('%E', bool, 'sendevent'),
    ('%K', str, 'keysym'),
    ('%N', int, 'keysym_num'),
    ('%P', str, 'property_name'),
    ('%R', int, 'root'),
    ('%S', int, 'subwindow'),
    ('%T', int, 'type'),
    ('%W', Widget, 'widget'),
    ('%X', int, 'rootx'),
    ('%Y', int, 'rooty'),
]


class Event:

    def __repr__(self):
        # try to avoid making the repr too verbose
        ignored_names = ['widget', 'sendevent', 'subwindow', 'time',
                         'i_window', 'root', 'state']
        ignored_values = [None, '??', -1, 0]

        pairs = []
        for name, value in sorted(self.__dict__.items(),
                                  key=operator.itemgetter(0)):
            if name not in ignored_names and value not in ignored_values:
                display_name = 'data' if name == '_data' else name
                pairs.append('%s=%r' % (display_name, value))

        return '<Event: %s>' % ', '.join(pairs)

    def data(self, type_spec):
        return from_tcl(type_spec, self._data)


class BindingDict(collections.abc.Mapping):

    # bind(3tk) calls things like '<Button-1>' sequences, so this code is
    # consistent with that
    def __init__(self, bind_caller, command_list):
        self._call_bind = bind_caller
        self.command_list = command_list
        self._callback_objects = {}     # {sequence: callback}

    def __repr__(self):
        return '<a bindings object, behaves like a dict>'

    def __iter__(self):
        # loops over all existing bindings, not all possible bindings
        return iter(self._call_bind([str]))

    def __len__(self):
        return len(self._call_bind([str]))

    def _callback_runner(self, callback, *args):
        assert len(args) == len(_BIND_SUBS)

        event = Event()
        for (character, type_, attrib), string_value in zip(_BIND_SUBS, args):
            assert isinstance(string_value, str)
            try:
                value = from_tcl(type_, string_value)
            except (ValueError, teek.TclError) as e:
                if string_value == '??':
                    value = None
                elif attrib == 'sendevent':
                    # this seems to be a bug in Tk, here's a minimal example:
                    #
                    #    label .lab -text "click this to do the bug"
                    #    pack .lab
                    #    bind .lab <Leave> { puts "leave: %E" }
                    #    bind .lab <Button-1> { tk_messageBox }
                    #
                    # for me this prints "leave: 343089580", even though
                    # bind(3tk) says that %E is 1 or 0
                    value = None
                else:   # pragma: no cover
                    raise e     # if this runs, there's a bug in teek

            setattr(event, attrib, value)

        return callback.run(event)

    def __getitem__(self, sequence):
        if sequence in self._callback_objects:
            return self._callback_objects[sequence]

        # <1> and <Button-1> are equivalent, this handles that
        for equiv_sequence, equiv_callback in self._callback_objects.items():
            # this equivalence check should handle corner cases imo because the
            # command names from create_command are unique
            if (self._call_bind(str, sequence) ==
                self._call_bind(str, equiv_sequence)):      # flake8: noqa
                # found an equivalent binding, tcl commands are the same
                self._callback_objects[sequence] = equiv_callback
                return equiv_callback

        callback = teek.Callback()
        runner = functools.partial(self._callback_runner, callback)
        command = teek.create_command(runner, [str] * len(_BIND_SUBS))
        self.command_list.append(command)      # avoid memory leaks

        subs_string = ' '.join(subs for subs, type_, name in _BIND_SUBS)
        self._call_bind(
            None, sequence, '+ if { [%s %s] eq {break} } { break }' % (
                command, subs_string))

        self._callback_objects[sequence] = callback
        return callback

    # any_widget.bind is set to this
    def _convenience_bind(self, sequence, func, *, event=False):
        self[sequence].connect(func if event else (lambda event: func()))


# TODO: "RELATIVE PLACEMENT" in grid(3tk)
class ChildMixin:
    """Mixin class for widgets that can be added to other widgets.

    Widgets like Label and Frame inherit from this, and widgets like
    Toplevel and Window don't. Many widgets use this, so it shouldn't be
    hard to find some usage examples for creating new widgets.
    """

    def _geometry_manage(self, geometry_manager, **kwargs):
        args = []
        for name, value in kwargs.items():
            if name == 'in_':
                name = 'in'
            args.append('-' + name)
            args.append(value)

        # special case: tkinter does nothing (lol), teek would give a
        # noob-unfriendly TclError otherwise
        if geometry_manager == 'place' and not args:
            raise TypeError(
                "cannot call widget.place() without any arguments, "
                "do e.g. widget.place(relx=0, rely=0) instead")

        self._call(None, geometry_manager, self.to_tcl(), *args)

    def _geometry_manager_forget(self, geometry_manager):
        self._call(None, geometry_manager, 'forget', self.to_tcl())

    def _geometry_manager_info(self, geometry_manager):
        types = {
            '-in': Widget,
        }

        if geometry_manager == 'pack' or geometry_manager == 'grid':
            types.update({
                # padx and pady can be lists of 2 screen distances or just 1
                # screen distance, which is fine because a Tcl screen distance
                # string
                # behaves like a list of 1 item
                '-padx': [teek.ScreenDistance],
                '-pady': [teek.ScreenDistance],
                '-ipadx': teek.ScreenDistance,
                '-ipady': teek.ScreenDistance,
            })

        if geometry_manager == 'pack':
            types.update({
                '-expand': bool,
            })
        elif geometry_manager == 'grid':
            types.update({
                '-column': int,
                '-columnspan': int,
                '-row': int,
                '-rowspan': int,
                '-sticky': str,
            })
        elif geometry_manager == 'place':
            types.update({
                '-anchor': str,
                '-bordermode': str,
                '-width': teek.ScreenDistance,
                '-height': teek.ScreenDistance,
                '-relheight': float,
                '-relwidth': float,
                '-relx': float,
                '-rely': float,
                '-x': teek.ScreenDistance,
                '-y': teek.ScreenDistance,
            })
        else:
            raise RuntimeError("oh no")     # pragma: no cover

        result = self._call(types, geometry_manager, 'info', self.to_tcl())
        return {key.lstrip('-'): value for key, value in result.items()}

    pack = functools.partialmethod(_geometry_manage, 'pack')
    grid = functools.partialmethod(_geometry_manage, 'grid')
    place = functools.partialmethod(_geometry_manage, 'place')

    pack_forget = functools.partialmethod(_geometry_manager_forget, 'pack')
    grid_forget = functools.partialmethod(_geometry_manager_forget, 'grid')
    place_forget = functools.partialmethod(_geometry_manager_forget, 'place')

    pack_info = functools.partialmethod(_geometry_manager_info, 'pack')
    grid_info = functools.partialmethod(_geometry_manager_info, 'grid')
    place_info = functools.partialmethod(_geometry_manager_info, 'place')
