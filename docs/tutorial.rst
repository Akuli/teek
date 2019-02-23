.. _tutorial:

Teek Tutorial
================

If you have never written any teek code before, you came to the right place.
**You don't need to have any tkinter experience** in order to learn teek,
although learning teek will be easier if you have used tkinter in the past.

.. note::
    If you have **any trouble at all** following this tutorial,
    `let me know <https://github.com/Akuli/teek/issues/new>`_ and I'll try
    to make this tutorial better. You can contact me for other things as well,
    but I'm especially interested in making this tutorial beginner-friendly.


.. _tcl-tk-tkinter-teek:

Tkinter, _tkinter, Tcl, Tk and teek
--------------------------------------

You need to install tkinter in order to install teek. That's correct,
teek is an alternative to tkinter that needs tkinter. This section explains
why.

When we say tkinter, we really mean a combination of two things that cannot be
installed separately:

* The ``_tkinter`` module that lets you run a Tcl interpreter within Python.
  **Tcl** is a programming language that can be used without ``_tkinter``.
* The pure-Python ``tkinter`` module uses ``_tkinter``. When you do something
  like ``root = tkinter.Tk()``, ``tkinter`` starts a Tcl interpreter using
  ``_tkinter``. Tkinter widgets are just classes written in pure Python that
  run commands in the Tcl interpreter; to be more precise, they use a Tcl
  library called **Tk**.

Teek is an alternative to the pure-Python part; it uses a Tcl interpreter
with ``_tkinter``, just like ``tkinter``, but it's much nicer to use in several
ways as shown in `the README <https://github.com/Akuli/teek/#teek>`_.

.. admonition:: tl;dr

    **Tcl** is a programming language with a nice GUI library named **Tk**.
    **Tkinter** and **Teek** both use Tcl and Tk with ``_tkinter``.


Installing Teek
------------------

Install Python 3.4 or newer and tkinter (yes, you need to have tkinter
installed, there are more details about this above). Then run this:

.. code-block:: none

    python3 -m pip install --user teek

Use ``py`` instead of ``python3`` if you are on Windows.


Hello World!
------------

::

    import teek

    window = teek.Window("Hello World")
    label = teek.Label(window, "Hello World!")
    label.pack()

    window.on_delete_window.connect(teek.quit)
    teek.run()

Run the program. It displays a tiny Hello World greeting.

Let's go through the program line by line.

::

    import teek

This imports teek. If you get an :exc:`ImportError` or a
:exc:`ModuleNotFoundError` from this step, make sure that you installed teek
as explained above.

You can also ``import teek as tk`` and use ``tk.Label`` instead of
``teek.Label``, but then people reading your code will see ``tk.Label`` there
and think that it's probably a tkinter label, because it's quite common to
``import tkinter as tk``. ``teek.Label`` is not much more work to type than
``tk.Label`` anyway (unlike ``tkinter.Label``), so I recommend just
``import teek``.

Don't do ``from teek import *`` because that confuses both tools that
process code automatically, and people who read your code.
``teek.Label(parent_widget, "hello")`` obviously creates a teek label, but
``Label(parent_widget, "hello")`` creates a label. What is a label? If you have
many star imports...

::

    # this code is BAD!! DONT DO THIS!! NO!!!
    from teek import *
    from os import *
    from sys import *

...and you need to find out where ``Label`` comes from, you have many things
that it might be coming from; if ``os`` or ``sys`` had something called
``Label``, it would replace teek's ``Label``. Everyone reading this code
need to know that neither ``os`` nor ``sys`` has anything named ``Label``,
which is bad. Also, if Python developers decide to add something called
``Label`` to ``os`` or ``sys``, your code will break.

::

    window = teek.Window("Hello World")

This creates a :class:`.Window` widget with title ``"Hello World"``. A widget is
an element of the GUI.

::

    label = teek.Label(window, "Hello World!")

Many widgets need to go into another widget. :class:`.Label` is a widget that
displays text, and this line of code puts it in our ``window``. The widget that
the label goes in is called the **parent** or the **master** widget of the
label. Similarly, the label is said to be a **child** or **slave** of the
window.

::

    label.pack()

If you create a label into the window, it isn't displayed automatically. This
line of code displays it.

Creating a child widget and displaying it in the parent are two separate things
because this way you can choose how the widget shows up. There's more
information about this :ref:`below <pack-with-frames>`.

::

    window.on_delete_window.connect(teek.quit)

This line tells teek to run :func:`teek.quit` when the window is closed. By
default, nothing happens when the user tries to close the window. You can
connect it to any other function or method as well, which is useful for things
like "Do you want to save your changes" dialogs.

::

    teek.run()

The code before this runs for just a fraction of a second, but this line of
code stays running until we close the window. That's usually something between
a few seconds and a few hours.

Note that instead of this...
::

    label = teek.Label(window, "Hello World")
    label.pack()

...we can also do this...
::

    teek.Label(window, "Hello World").pack()

...because we create the variable once, and only use it once. However, this
doesn't work::

    label = teek.Label(window, "Hello World").pack()    # WRONG! common mistake

Look carefully: this does *not* set the ``label`` variable to a label; it sets
that variable to what ever ``the_actual_label_widget.pack()`` returns, which is
*not* same as the label widget itself. If you need to do more than one thing to
a widget, set that widget to a variable and do all the things to that variable.


.. _options:

Options
-------

Widget options can be used to change how widgets look and behave. For example,
the text of a label is in an option named ``text``.

>>> window = teek.Window()
>>> label = teek.Label(window, "blah blah")
>>> label.config['text']
'blah blah'

The only way to check the value of an option is ``label.config['text']``, but
you can set values of options in several ways:

* You can change the text after creating the label like
  ``label.config['text'] = "new text"``. The label will display the new text
  automatically.
* When creating the label, you can pass options to it like
  ``teek.Label(window, text="blah blah")``. Some common options can also be used
  without passing the option name explicitly with ``text=``, e.g.
  ``teek.Label(window, "blah blah")``. This is widget-specific, and it's
  documented in teek's documentation; for example, this label thing is
  documented in :class:`.Label` docs.

Sometimes the name of a widget option happens to be a reserved keyword in
Python. For example, ``in`` is not a valid Python variable name because it's
used in things like ``'hello' in 'hello world'``:

>>> in = 'lol'
Traceback (most recent call last):
  ...
SyntaxError: invalid syntax
>>> label.pack(in=window)
Traceback (most recent call last):
  ...
SyntaxError: invalid syntax

To avoid this problem, you can use ``in_`` instead of ``in``, and teek will
handle it correctly:

>>> in_ = 'lol'
>>> in_
'lol'
>>> label.pack(in_=window)

Teek strips the last ``_`` before it does anything with the option.


Tkinter Instructions
--------------------

Tkinter is very popular, so if you want to know how to do something in tkinter,
you can just google it. For example, if you want to change the text of a label
after creating it, google "tkinter change label text" and you'll find a
stackoverflow answer that does ``some_label['text'] = 'new text'`` and
``some_label.config(text='new text')``. Neither of those works in teek, but
both of them give errors with good messages that tell you what you need
to do instead.

Sometimes teek and tkinter differ a lot more, and teek can't detect too
tkintery ways to do things and give you particularly good errors. In these
cases, use :ref:`teek's tkinter porting guide <tkinter>`.


.. _man-pages:

Manual Pages
------------

.. note::
    This section assumes that you know the Tcl stuff explained
    :ref:`above <tcl-tk-tkinter-teek>`.

Sometimes stackoverflow answers don't contain the best possible solution
because they are written by noobs who don't actually know Tk and tkinter very
well. I see this quite often. Some of the people who answer tkinter questions
on stackoverflow have 20+ years of :ref:`Tk <tcl-tk-tkinter-teek>`
experience, but most answerers don't.

If you don't want to rely on stackoverflow or you want to do things like
experienced Tk programmers do things, you should read Tk's manual pages. They
are written for Tcl users and Tcl's syntax is quite different from Python
syntax, so you will probably be somewhat confused at first. For example, let's
say that you don't know how to change the text of a label after creating it.
Figure it out like this:

1. Go to teek's label documentation by clicking this :class:`.Label` link.
   This tutorial and rest of teek's documentation are full of these links.
   Click them.
2. The :class:`.Label` link doesn't say anything about changing the text
   afterwards, but it has a link to a manual page. Click it.
3. In the manual page, press Ctrl+F and search for "text". You'll find a widget
   option whose "Command-Line Name" is ``-text``. The leading ``-`` is common
   in Tcl syntax, but we won't need it in teek. So all we really need to do
   is to change the ``'text'`` widget option as shown :ref:`above <options>`.
   We found what we were looking for.

.. admonition:: BTW

    The manual page names are like :man:`ttk_label(3tk)` or :man:`after(3tcl)`.
    GUI things have ``3tk`` manual pages, and things documented in ``3tcl``
    manual pages can be also used in Tcl programs that don't have a GUI.

If you use Linux, you can also install the manual pages on your system and read
them without a web browser. For example, this command installs them on ubuntu:

.. code-block:: shell

    sudo apt install tcl8.6-doc tk8.6-doc

The ``8.6`` makes sure that you get newest manual pages available. After
installing the manual pages, you can read them like this:

.. code-block:: shell

    man ttk_label

You can close the manual page by pressing q like quit. If you want to search,
Ctrl+F won't work, but instead you can type ``/text`` followed by enter to
search for ``text``. All matches will be highlighted, and you can press n like
next to go to the next match.


Buttons and callback functions
------------------------------

This code displays a button. Clicking the button runs the ``on_click()``
function.
::

    import teek

    def on_click():
        print("You clicked me!")

    window = teek.Window("Button Example")
    button = teek.Button(window, "Click me", command=on_click)
    button.pack()

    window.on_delete_window.connect(teek.quit)
    teek.run()

Most of the code isn't very different from our label example. Let's go through
the things that are different.
::

    def on_click():
        print("You clicked me!")

This defines a function. If you have never defined functions before, you should
*definitely* learn that before continuing with this tutorial. It'll make
everything a lot easier. I have written more about defining functions here_.

.. _here: https://github.com/Akuli/python-tutorial/blob/master/basics/defining-functions.md

::

    button = teek.Button(window, "Click me", command=on_click)

:class:`.Button` takes a parent widget and a text, just like :class:`.Label`,
but :class:`.Button` also takes a function that is called when the button is
clicked. Read that sentence carefully: :class:`.Button` takes a **function**.
This is a common mistake::

    button = teek.Button(..., command=on_click())     # ummm... it doesn't work like this!!

``command=on_click()`` does not do what was intended here;
``command=on_click()`` calls the ``on_click`` function because it has ``()``
after ``on_click``, and when ``on_click`` has been called, it creates the
button and passes the return value of ``on_click`` to it. Be careful to pass
the function itself without calling it.

.. admonition:: BTW

    Teek lets you omit the ``command=`` part when creating buttons if you
    put the button text before the command, so this...
    ::

        button = teek.Button(window, "Click me", on_click)

    ...does the same thing as this::

        button = teek.Button(window, "Click me", command=on_click)

Here is another common mistake::

    import time

    def on_click():
        print("Doing something...")
        time.sleep(5)
        print("Done")

Here ``time.sleep(5)`` waits for 5 seconds. If you click the button now, the
GUI will be frozen for 5 seconds. The button will look like it's pressed down,
and you can't even close the window! This is bad, and that's why button
callbacks must not do anything that takes longer than a tiny fraction of a
second. See :ref:`concurrency documentation <concurrency>` if you need a button
callback that runs for a long time.


.. _pack-with-frames:

Multiple child widgets in same parent
-------------------------------------

It's possible to put several different widgets into the same parent window with
:meth:`~.Widget.pack`, like this::

    import teek

    window = teek.Window("Pack Example")
    teek.Label(window, "One").pack()
    teek.Label(window, "Two").pack()

    window.on_delete_window.connect(teek.quit)
    teek.run()

The "Two" label will show up below the "One" label. If you don't want that, you
can also put the labels next to each other::

    teek.Label(window, "One").pack(side='left')
    teek.Label(window, "Two").pack(side='left')

That's correct, both of them have ``side='left'``. This means that the first
widget goes all the way to the left edge, and the second goes to the *right* of
that, and so on, so the widgets get stacked to the left edge. The default is
``side='top'``, and that's why the widgets ended up below each other.

If you need more complex layouts, you can create a :class:`.Frame` and pack it,
and add more widgets *inside* that :class:`.Frame`, like this::

    import teek

    window = teek.Window("Pack Example")

    big_frame = teek.Frame(window)
    big_frame.pack(fill='both', expand=True)
    teek.Label(big_frame, text="Left").pack(side='left', fill='both', expand=True)
    teek.Label(big_frame, text="Right").pack(side='left', fill='both', expand=True)

    status_bar = teek.Label(window, "This is a status bar")
    status_bar.pack(fill='x')

    window.geometry(300, 200)
    window.on_delete_window.connect(teek.quit)
    teek.run()

This example uses plenty of things from :man:`pack(3tk)`, but you know
:ref:`how to read manual pages <man-pages>`, so you can figure out how it all
works. If that isn't true at all, keep reading, and I'll explain how some of
the things in the example work.

::

    big_frame.pack(fill='both', expand=True)

This packs the big frame so that it stretches if you resize the window, and it
fills as much space as possible. If you don't want to learn everything about
pack, learn at least this "idiom".

::

    status_bar.pack(fill='x')

This makes the status bar fill all the space it has horizontally.
Mathematicians like to call it the ``x`` direction. Use ``fill='y'`` to fill
vertically, or ``fill='both'`` to fill in both ``x`` and ``y`` directions.

::

    window.geometry(300, 200)

This call to :meth:`~.Toplevel.geometry` resizes the window so that it's bigger
by default, and you can see how the widgets got laid out without first making
the window bigger.


What now?
---------

You are ready for creating a project in teek! All parts of teek's
documentation are listed at left, but here are the things you will most
likely need next:

* :ref:`widgets`
* :ref:`geometry-managers`
