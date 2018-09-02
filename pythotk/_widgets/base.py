import collections.abc
import contextlib
import functools
import operator
import re

import pythotk as tk
from pythotk._tcl_calls import counts, from_tcl, needs_main_thread
from pythotk._structures import CgetConfigureConfigDict, on_quit

_widgets = {}
on_quit.connect(_widgets.clear)


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
    with :func:`isinstance`; e.g. ``isinstance(thingy, tk.Widget)`` returns
    ``True`` if ``thingy`` is a pythotk widget.

    .. attribute:: config

        A dict-like object that represents the widget's options.

        >>> window = tk.Window()
        >>> label = tk.Label(window, text='Hello World')
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
    """

    def __init__(self, widgetname, parent, **options):
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
        self._call(None, widgetname, self.to_tcl())
        _widgets[self.to_tcl()] = self

        self.config = CgetConfigureConfigDict(
            lambda returntype, *args: self._call(returntype, self, *args))
        self.config._types.update({
            # ttk_widget(3tk)
            'class': str,
            'cursor': str,
            'style': str,
            'width': tk.ScreenDistance,

            # options(3tk)
            'activebackground': tk.Color,
            'activeborderwidth': tk.ScreenDistance,
            'activeforeground': tk.Color,
            'anchor': str,
            'background': tk.Color,
            'bg': tk.Color,
            #'bitmap': ???,
            'borderwidth': tk.ScreenDistance,
            'bd': tk.ScreenDistance,
            'cursor': str,
            'compound': str,
            'disabledforeground': tk.Color,
            'exportselection': bool,
            'font': tk.Font,
            'foreground': tk.Color,
            'fg': tk.Color,
            'highlightbackground': tk.Color,
            'highlightcolor': tk.Color,
            'highlightthickness': str,
            'insertbackground': tk.Color,
            'insertborderwidth': tk.ScreenDistance,
            'insertofftime': int,
            'insertontime': int,
            'insertwidth': tk.ScreenDistance,
            'jump': bool,
            'justify': str,
            'orient': str,
            'padx': tk.ScreenDistance,
            'pady': tk.ScreenDistance,
            'relief': str,
            'repeatdelay': int,
            'repeatinterval': int,
            'selectbackground': tk.Color,
            'selectborderwidth': tk.ScreenDistance,
            'selectforeground': tk.Color,
            'setgrid': bool,
            'text': str,
            'troughcolor': tk.Color,
            'wraplength': tk.ScreenDistance,

            # these options are in both man pages
            'textvariable': tk.StringVar,
            'underline': int,
            'image': tk.Image,
            # 'xscrollcommand' and 'yscrollcommand' are done below
            'takefocus': str,   # this one is harder to do right than you think

            # other stuff that many things seem to have
            'height': tk.ScreenDistance,
            'padding': tk.ScreenDistance,
            'state': str,
        })
        for option_name in ('xscrollcommand', 'yscrollcommand'):
            self.config._special[option_name] = functools.partial(
                self._create_scroll_callback, option_name)

        self.config.update(options)

        # command strings that are deleted when the widget is destroyed
        self._command_list = []

        self.bindings = BindingDict(    # BindingDict is defined below
         lambda returntype, *args: self._call(returntype, 'bind', self, *args),
         self._command_list)

    @classmethod
    def from_tcl(cls, path_string):
        """Creates a widget from a Tcl path names.

        In Tcl, widgets are represented as commands, and doing something to the
        widget invokes the command. Use this method if you know the Tcl command
        and you would like to have a widget object instead.

        This method raises :exc:`TypeError` if it's called from a different
        ``Widget`` subclass than what the type of the ``path_string`` widget
        is:

        >>> window = tk.Window()
        >>> tk.Button.from_tcl(tk.Label(window).to_tcl())  # doctest: +ELLIPSIS
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
        if getattr(tk, class_name, None) is type(self):
            result = 'pythotk.%s widget' % class_name
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
        result = tk.Callback(float, float)
        command_string = tk.create_command(result.run, [float, float])
        self._command_list.append(command_string)
        self._call(None, self, 'configure', '-' + option_name, command_string)
        return result

    __getitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    __setitem__ = _tkinter_hint("widget.config['option']", "widget['option']")
    cget = _tkinter_hint("widget.config['option']", "widget.cget('option')")
    configure = _tkinter_hint("widget.config['option'] = value",
                              "widget.configure(option=value)")

    def bind(self, sequence, func, *, event=False):
        """
        For convenience, ``widget.bind(sequence, func, event=True)`` does
        ``widget.bindings[sequence].connect(func)``.

        If ``event=True`` is not given, ``widget.bindings[sequence]`` is
        connected to a new function that calls ``func`` with no arguments,
        ignoring the event object.

        .. note::
            In tkinter, ``widget.bind(sequence, func)`` discards all old
            bindings, and if you want to bind multiple functions to the same
            sequence, you need to specifically tell it to not discard anything.
            I have no idea why tkinter does that. Pythotk keeps the old
            bindings because the :class:`.Callback` does that.
        """
        eventy_func = func if event else (lambda event: func())
        self.bindings[sequence].connect(eventy_func)

    # like _tcl_calls.tcl_call, but with better error handling
    @needs_main_thread
    def _call(self, *args, **kwargs):
        try:
            return tk.tcl_call(*args, **kwargs)
        except tk.TclError as err:
            if not self.winfo_exists():
                raise RuntimeError("the widget has been destroyed") from None
            raise err

    # TODO: document overriding this
    def destroy(self):
        """Delete this widget and all child widgets.

        Manual page: :man:`destroy(3tk)`
        """
        for name in self._call([str], 'winfo', 'children', self):
            # allow overriding the destroy() method if the widget was
            # created by pythotk
            if name in _widgets:
                _widgets[name].destroy()
            else:
                self._call(None, 'destroy', name)

        for command in self._command_list:
            tk.delete_command(command)
        self._command_list.clear()      # why not

        self._call(None, 'destroy', self)
        del _widgets[self.to_tcl()]

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
        return tk.tcl_call(bool, 'winfo', 'exists', self)

    def winfo_toplevel(self):
        """Returns the :class:`Toplevel` widget that this widget is in.

        Manual page: :man:`winfo(3tk)`
        """
        return self._call(Widget, 'winfo', 'toplevel', self)

    def pack_slaves(self):
        return self._call([Widget], 'pack', 'slaves', self)

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
        pythotk.
        """
        option_args = []
        for name, value in kwargs.items():
            option_args.extend(['-' + name, value])
        self._call(None, 'event', 'generate', self, event, *option_args)


# these are from bind(3tk), Tk 8.5 and 8.6 support all of these
# the ones marked "event(3tk)" use names listed in event(3tk), and "tkinter"
# ones use same names as tkinter's event object attributes
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
        self._command_list = command_list
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
            except (ValueError, tk.TclError) as e:
                if string_value == '??':
                    value = None
                else:
                    raise e

            setattr(event, attrib, value)

        callback.run(event)

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

        callback = tk.Callback(Event)
        runner = functools.partial(self._callback_runner, callback)
        command = tk.create_command(runner, [str] * len(_BIND_SUBS))
        self._command_list.append(command)      # avoid memory leaks

        self._call_bind(None, sequence, '+%s %s' % (
            command, ' '.join(subs for subs, type_, name in _BIND_SUBS)))
        self._callback_objects[sequence] = callback
        return callback


class ChildMixin:

    def pack(self, **kwargs):
        args = []
        for name, value in kwargs.items():
            if name == 'in_':
                name = 'in'
            args.append('-' + name)
            args.append(value)
        self._call(None, 'pack', self.to_tcl(), *args)

    def pack_forget(self):
        self._call(None, 'pack', 'forget', self.to_tcl())

    def pack_info(self):
        types = {
            # padx and pady can be lists of 2 screen distances or just 1 screen
            # distance, which is fine because a Tcl screen distance string
            # behaves like a list of 1 item, that screen distance string
            '-padx': [tk.ScreenDistance],
            '-pady': [tk.ScreenDistance],
            '-ipadx': tk.ScreenDistance,
            '-ipady': tk.ScreenDistance,
            '-in': Widget,
            '-expand': bool,
        }
        result = self._call(types, 'pack', 'info', self.to_tcl())
        return {key.lstrip('-'): value for key, value in result.items()}
