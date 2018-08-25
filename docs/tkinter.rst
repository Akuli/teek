Porting from Tkinter
====================

If you have some tkinter code and you would like to switch to pythotk, you came
to the right place. This page lists differences between tkinter and pythotk.
You might also find this page interesting if you are an experienced tkinter
programmer.


Before you begin
----------------

Make sure you have good test coverage. If you don't know what test coverage is,
I hope your project is quite small. In that case, make sure that you know how
every part and feature of the GUI is supposed to work and how to check if it
works well. Running a linter like flake8_ may also help, and understanding how
the code works doesn't hurt either.

.. _flake8: http://flake8.pycqa.org/en/latest/

Currently these tkinter widgets are missing in pythotk:

* ``tkinter.Canvas``
* ``tkinter.Checkbutton``, ``tkinter.ttk.Checkbutton``
* ``tkinter.Entry``, ``tkinter.ttk.Entry``
* ``tkinter.LabelFrame``, ``tkinter.ttk.Labelframe``
* ``tkinter.Listbox``
* ``tkinter.Menu``
* ``tkinter.Menubutton``, ``tkinter.ttk.Menubutton``
* ``tkinter.ttk.Notebook``
* ``tkinter.OptionMenu``
* ``tkinter.PanedWindow``, ``tkinter.ttk.Panedwindow``
* ``tkinter.ttk.Progressbar``
* ``tkinter.Radiobutton``, ``tkinter.ttk.Radiobutton``
* ``tkinter.Scale``, ``tkinter.ttk.Scale``
* ``tkinter.Scrollbar``, ``tkinter.ttk.Scrollbar``
* ``tkinter.ttk.Separator``
* ``tkinter.ttk.Sizegrip``
* ``tkinter.Spinbox``
* ``tkinter.ttk.Treeview``

If the project uses some of these, you can still use them with
:ref:`Tcl calls <tcl-calls>`. However, that's kind of painful, so if the
project uses these widgets a lot, it's probably best to use tkinter for now or
`ask me <https://github.com/Akuli/pythotk/issues/new>`_ to add the widget to
pythotk.


To Get Started
--------------

If you find a file that contains ``from tkinter import *``, you should
immediately fix that. It is very bad style. Change the import to
``import pythotk as tk``, and then replace things like ``Label`` with
``tk.Label``.

If you find code like ``import tkinter as tk``, just change ``tkinter`` to
``pythotk``. If there is ``import tkinter``, replace ``tkinter.something`` with
``tk.something`` everywhere and ``import pythotk as tk``.

Sometimes you may see this::

    import tkinter as tk
    from tkinter import ttk

Or much worse::

    from tkinter import *
    from tkinter.ttk import *

In these cases, you should replace both ``tkinter.something`` and
``tkinter.ttk.something`` with ``tk.something`` and do the
``import pythotk as tk``. Pythotk contains ttk widgets as needed.

After this, try it out. It probably doesn't work yet, so keep reading.


Widget Name Differences
-----------------------

All tkinter GUIs use a ``tkinter.Tk`` object. There is no ``Tk`` object in
pythotk; usually you should instead create a :class:`.Window` object and use
that. Also use :class:`.Window` instead of a ``tkinter.Toplevel``; you can
create as many pythotk windows as you want, and they actually use toplevels
under the hood.

Other widgets should be named the same as in tkinter.

If you have code that uses ``tkinter.Message``, you should use a ``Label``
instead. I believe message widgets were a thing before labels could handle
multiline text, but nowadays the text of labels can contain ``\n`` characters.


Different Options
-----------------

Options are used differently in tkinter and pythotk. For example,
``button['text']``, ``button.cget('text')``, ``button.config('text')[-1]`` and
``button.configure('text')[-1]`` are all valid ways to get the text of a label.
In pythotk, none of these works, and you instead do ``button.config['text']``.
However, pythotk raises good error messages when you try to do something that
is not compatible with tkinter:

>>> button = tk.Button(tk.Window(), "some text")
>>> button.cget('text')
Traceback (most recent call last):
    ...
TypeError: use widget.config['option'], not widget.cget('option')
>>> button['text']
Traceback (most recent call last):
    ...
TypeError: use widget.config['option'], not widget['option']
>>> button.config['text']
'some text'

Some things are done differently in tkinter and pythotk. For example, tkinter
buttons have a ``command`` option that is set to a function that runs when the
button is clicked, but pythotk doesn't have that:

>>> button.config['command'] = print
Traceback (most recent call last):
    ...
ValueError: the 'command' option is not supported, use the on_click attribute or an initialization argument instead

The code looks like this with :attr:`~.Button.on_click`:

>>> button.on_click.connect(print)

In general, refer to :ref:`the documentation <widgets>` of the widget that is
causing errors.


Binding
-------

Pythotk's bind stuff is documented :ref:`here <binding>`. As you can see there,
we have some differences to tkinter. First of all, if you want anything to work
at all, you need to pass ``event=True`` to :meth:`~.Widget.bind` to get
tkinter-like event objects. However, this is a common thing to do in tkinter::

    widget.bind('<SomeEvent>', lambda event: some_function())

Tkinter always gives an ``event`` argument to bind callbacks, and the lambda
discards it because ``some_function`` must be called like ``some_function()``,
not ``some_function(event)``. If you just pass ``event=True``, you end up with
code like this...
::

    widget.bind('<SomeEvent>', (lambda event: some_function()), event=True)

...which can be simplified a lot because not using ``event=True`` does the same
thing as the lambda::

    widget.bind('<SomeEvent>', some_function)

If you do need the event object, watch out for differences in the attributes.
For example, tkinter's ``event.x_root`` is ``event.rootx`` in pythotk. This is
for consistency with :meth:`~.Widget.event_generate`.

Note that tkinter's ``bind`` discards all old bindings, but this doesn't happen
in pythotk. For example, if you do this...
::

    widget.bind('<SomeEvent>', func1)
    widget.bind('<SomeEvent>', func2)

...only ``func2`` is bound in tkinter, but both are bound in pythotk.

Tkinter's bind takes an ``add=True`` argument that tells it to not forget old
bindings, and you can safely get rid of it. If you see some tkinter code that
relies on the discarding behaviour, which I don't see very often, you need to
use :attr:`.Widget.bindings` to unbind the old function.

Speaking of unbinding, tkinter also has an ``unbind()`` method. It works like
this when used correctly::

    func_id = widget.bind('<SomeEvent>', func)
    ...
    widget.unbind('<SomeEvent>', func_id)

Searching for ``def unbind`` in
`tkinter's source code <https://github.com/python/cpython/blob/master/Lib/tkinter/__init__.py>`_
reveals that ``widget.unbind`` actually discards all bindings of
``<SomeEvent>``, and if the ``func_id`` is given, it also cleans things up.
Pythotk does the cleanup automatically for you when the widget is destroyed
(see :meth:`~.Widget.destroy`).


Text Widgets
------------

Many things are different (read: much better and more pythonic) in pythotk than
in tkinter. You probably need to read most of pythotk's
:ref:`text widget docs <textwidget>` anyway, so I won't even try to summarize
everything here.


Font Objects
------------

Tkinter has one font class, ``tkinter.font.Font``, which represents a font that
has a name in Tcl. There are two font classes in pythotk, and usually you
should use :class:`.NamedFont` in pythotk when ``tkinter.font.Font`` is used in
tkinter. See :ref:`font documentation <font-objs>` for details.


Tcl Calls
---------

In tkinter, you might see code like this::

    if root.tk.call('tk', 'windowingsystem') == 'aqua':
        ...some mac specific code...

Here ``root.tk.call('tk', 'windowingsystem')`` calls ``tk windowingsystem`` in
Tcl, and that returns ``'win32'``, ``'aqua'`` or ``'x11'`` as documented in
:man:`tk(3tk)`. Notice that the return type is a string, but it's not specified
anywhere. Pythotk is more explicit::

    if tk.tcl_call(str, 'tk', 'windowingsystem') == 'aqua':
        ...

``1.2 == '1.2'`` is false in python, but there is no distinction like that in
Tcl; all objects are essentially strings, and ``1.2`` is literally the same
thing as ``'1.2'``. There is no good way to figure out what type tkinter's
``root.tk.call`` will return, and it's easiest to try it and see.

Pythotk gets rid of this problem by requiring explicit return types everywhere.
If you want a Tcl call to return a string, you pass it ``str``. See
:ref:`tcl-calls` for more documentation.


Dialogs
-------

Dialog functions are named differently in pythotk. For example, instead of
``filedialog.askopenfilename()`` you use
:func:`tk.dialog.open_file() <.dialog.open_file>`. Unlike in tkinter, you don't
need to import anything special in order to use the dialog functions;
``import pythotk as tk`` is all you need, and after that, you can do
``tk.dialog.open_file()``.
