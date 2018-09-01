.. _binding:

Binding
=======

:class:`.Button` widgets have a ``'command'`` option, and that is set to a
callback that runs when the button is clicked. But what if you have some other
widget instead of a button, and you want to do something when it's clicked?
This can be useful; for example, my editor displays its logo in the about
dialog, and if the logo is clicked, it shows the logo in full size.

Bindings are not limited to just clicking. You can bind to some other things as
well, such as mouse movement and key presses.


Simple Example
--------------

This program displays a label that prints hello when it's clicked.
::

    import pythotk as tk

    def on_click():
        print("hello")

    window = tk.Window()
    label = tk.Label(window, "Click me")
    label.pack()
    label.bind('<Button-1>', on_click)
    tk.run()

If you change ``'<Button-1>'`` to ``'<Motion>'``, ``'hello'`` is printed every
time you move the mouse over the label. See :man:`bind(3tk)` for all possible
strings you can pass to :meth:`~.Widget.bind`.


Event Objects
-------------

In Tcl, code like this...

.. code-block:: tcl

    bind $widget <Button-1> {puts "clicked at %X,%Y"}

...means that if the widget is clicked 10 pixels right and 20 pixels down from
the top left corner of the widget's parent window, ``clicked at 10,20`` will be
printed. Here ``puts "clicked at %X,%Y"`` is a string of code, and ``%X`` and
``%Y`` are replaced with the coordinates before it's ran.

This pythotk code does the same thing::

    def on_click(event):
        print("clicked at {},{}".format(event.rootx, event.rooty))

    widget.bind('<Button-1>', on_click, event=True)

Here ``on_click()`` gets an event object. It has attributes that describe what
happened, like ``rootx`` and ``rooty``. If you don't pass ``event=True``, the
callback will be called without the event object.

The ``%X`` and ``%Y`` stuff is documented in :man:`bind(3tk)`, but
:man:`event(3tk)` seems to contain more useful things. Event object attributes
are named similarly as in :man:`event(3tk)`; for example, there is a ``-rootx``
option in :man:`event(3tk)`, and that's why pythotk's event objects have a
``rootx`` attribute.

Here is a long table of attributes that pythotk supports. It took me a long
time to make. The list also demonstrates how limited tkinter is; only a few
things in this table are supported in tkinter.

.. |br| raw:: html

    <br>

+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| Name in :man:`event(3tk)` and |br| pythotk event attribute            | Type in pythotk           | Tkinter event |br| attribute, if any  | Tcl substitution |br| :man:`bind(3tk)`|
+=======================================================================+===========================+=======================================+=======================================+
| ``above``                                                             | ``int``                   |                                       | ``%a``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``borderwidth``                                                       | ``int``                   |                                       | ``%B``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``button``                                                            | ``int``                   | ``num``                               | ``%b``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``char`` in pythotk                     | ``str``                   | ``char``                              | ``%A``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``count``                                                             | ``int``                   |                                       | ``%c``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``data``                                                              | see :ref:`virtual-event`  |                                       | ``%d``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``detail`` in :man:`event(3tk)` |br| ``event.data(str)`` in pythotk   | ``str``                   |                                       | ``%d``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``delta``                                                             | ``int``                   | ``delta``                             | ``%D``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``focus``                                                             | ``bool``                  | ``focus``                             | ``%f``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``height``                                                            | ``int``                   | ``height``                            | ``%h``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``i_window`` in pythotk                 | ``int``                   |                                       | ``%i``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``keycode``                                                           | ``int``                   | ``keycode``                           | ``%k``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``keysym``                                                            | ``str``                   | ``keysym``                            | ``%K``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``keysym_num`` in pythotk               | ``int``                   | ``keysym_num``                        | ``%N``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``mode``                                                              | ``str``                   |                                       | ``%m``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``override``                                                          | ``bool``                  |                                       | ``%o``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``place``                                                             | ``str``                   |                                       | ``%p``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``property_name`` in pythotk            | ``str``                   |                                       | ``%P``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``root``                                                              | ``int``                   |                                       | ``%R``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``rootx``                                                             | ``int``                   | ``x_root``                            | ``%X``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``rooty``                                                             | ``int``                   | ``y_root``                            | ``%Y``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``sendevent``                                                         | ``bool``                  | ``send_event``                        | ``%E``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``serial``                                                            | ``int``                   | ``serial``                            | ``%#``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``state``                                                             | ``str``                   | ``state``                             | ``%s``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``subwindow``                                                         | ``int``                   |                                       | ``%S``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``time``                                                              | ``int``                   | ``time``                              | ``%t``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``type`` in pythotk                     | ``int``                   | ``type``                              | ``%T``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| not in :man:`event(3tk)` |br| ``widget`` in pythotk                   | :class:`.Widget`          | ``widget``                            | ``%W``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``width``                                                             | ``int``                   | ``width``                             | ``%w``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``x``                                                                 | ``int``                   | ``x``                                 | ``%x``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+
| ``y``                                                                 | ``int``                   | ``y``                                 | ``%y``                                |
+-----------------------------------------------------------------------+---------------------------+---------------------------------------+---------------------------------------+

Note that ``%d`` is used for both ``detail`` and ``data`` in Tcl, depending on
the type of the event. Pythotk uses that internally, but it doesn't keep track
of the event types for you, so you need to do ``event.data(str)`` if you want
the ``detail`` string.

.. note::
    If the value is not available, it's usually None, but the attributes whose
    pythotk type is ``str`` are ``'??'`` instead. The reason is that the Tcl
    substitution gets a ``??`` value for some reason in these cases, but
    ``'??'`` could be also a valid value of e.g. ``data``, so pythotk doesn't
    try to hide it.

The "Tcl bind substitution" and "tkinter event attribute" columns are for
porting Tcl code and tkinter code to pythotk. If you are writing a new program
in pythotk, don't worry about them.


The bindings attribute
----------------------

Pythotk uses :class:`.Callback` objects for most things that it runs for you.
It also does that with bindings.

.. attribute:: pythotk.Widget.bindings

    A dictionary-like object of the widget's bindings with string keys and
    :class:`.Callback` values.

    Some binding sequences are equivalent in Tk. For example,
    ``<ButtonPress-1>``, ``<Button-1>`` and ``<1>`` all mean the same thing,
    and looking up those strings from a widget's ``bindings`` is guaranteed
    to give the same :class:`.Callback` object.

.. automethod:: pythotk.Widget.bind


.. _virtual-event:

Virtual Events
--------------

Names of virtual events have ``<<`` and ``>>`` instead of ``<`` and ``>``. Here
is an example:

>>> window = tk.Window()
>>> label = tk.Label(window)
>>> label.bind('<<Asd>>', print, event=True)   # will run print(the_event)
>>> label.event_generate('<<Asd>>')     # doctest: +ELLIPSIS
<Event: data='', serial=..., type=35>

You can also pass data to the virtual event:

>>> label.event_generate('<<Asd>>', data='toot')     # doctest: +ELLIPSIS
<Event: data='toot', serial=..., type=35>

If you want to actually use the data, don't do just ``event.data``; that
doesn't work right. Instead, use ``event.data(type_spec)`` where ``type_spec``
is a :ref:`type specifacion <type-spec>`. For example, ``event.data([str])``
retrieves the data as a list of strings.

>>> def callback(event):
...     print("got data string list:", event.data([str]))
...
>>> label.bind('<<ThingyThing>>', callback, event=True)
>>> label.event_generate('<<ThingyThing>>', data=['a', 'b', 'c'])  # doctest: +ELLIPSIS
got data string list: ['a', 'b', 'c']

.. automethod:: pythotk.Widget.event_generate
