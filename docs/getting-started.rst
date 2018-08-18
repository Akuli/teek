.. _getting-started:

Getting Started with Pythotk
============================

This page shows you some basic things you need to know when programming with
pythotk.


Installation
------------

Install Python 3.4 or newer and tkinter (yes, you need to have tkinter
installed, there are more details about this below). Then run this:

.. code-block:: none

    python3 -m pip install --user git+https://github.com/Akuli/pythotk

Use ``py`` instead of ``python3`` if you are on Windows.

You need to have ``git`` installed for the above command. If you don't have
git, you can use this command instead:

    python3 -m pip install --user https://github.com/Akuli/pythotk/archive/master.zip


Tkinter, _tkinter, Tcl, Tk and PythoTk
--------------------------------------

After reading this section, you'll know why you needed to install tkinter in
order to install pythotk.

When we say tkinter, we really mean a combination of two things that cannot be
installed separately:

* The ``_tkinter`` C extension module that lets you run a Tcl interpreter
  within Python. **Tcl** is a programming language that can be used without
  ``_tkinter``.
* The pure-Python ``tkinter`` module. This module uses ``_tkinter``. When you
  do something like ``root = tkinter.Tk()``, ``tkinter`` starts a Tcl
  interpreter using ``_tkinter``. Tkinter widgets are just classes written in
  pure Python that run commands in the Tcl interpreter; to be more precise,
  they use a Tcl library called **Tk**.

Pythotk is an alternative to the pure-Python part; it uses a Tcl interpreter
with ``_tkinter``, just like ``tkinter``, but it's much nicer to use in several
ways as shown in `the README <https://github.com/Akuli/pythotk/#pythotk>`_.

.. note::
    You don't need to know how to use ``tkinter`` in order to program with
    ``pythotk``. You don't need to have any experience with Tcl either, but if
    you have used Tcl before, it will help you, especially with more advanced
    things like :ref:`Tcl calls <tcl-calls>`.

.. admonition:: tl;dr

    **Tcl** is a programming language with a nice GUI library named **Tk**.
    **Tkinter** and **PythoTk** both use Tcl and Tk with ``_tkinter``.


Importing
---------

::

    import pythotk as tk

That's it. Don't use e.g. ``from pythotk import *`` because that confuses both
tools that process code automatically, and people who read your code:
``tk.Label(parent_widget, "hello")`` obviously creates a tk label, but
``Label(parent_widget, "hello")`` creates a label. What is a label? If you have
many star imports...

::

    # this code is BAD!! DONT DO THIS!! NO!!!
    from pythotk import *
    from os import *
    from sys import *

...you have no idea where the ``Label`` comes from (unless you happen to know
that ``pythotk`` has a class named ``Label`` **AND** ``os`` and ``sys`` don't
have anything named ``Label``.

You can also import ``pythotk`` and use ``pythotk.Label`` instead of
``tk.Label``, but most pythotk programs use pythotk things a lot, and it's much
easier to ``import pythotk as tk``.

.. important::
    From now on, if you see ``tk.something`` in this documentation, it means
    ``pythotk.something``.


.. _man-pages:

Manual Pages
------------

Pythotk and tkinter are both ways to use Tk in Python. Tk is a library written
for a programming language called Tcl, so the official documentation of most
things is written in Tcl. Tkinter documentation is mostly copy/pasted from
Tcl's documentation, but I don't like copy/pasting stuff, so in pythotk you
will need to read the Tcl documentation yourself. This is a good thing because
copy/pasting would also mean that pythotk documentation is not updated when a
new feature is added to Tk, which is a problem with tkinter's documentation.

To make reading Tcl documentation easier, pythotk's documentation contains
links to Tcl and Tk manual pages, like :man:`after(3tcl)` or
:man:`ttk_label(3tk)`.

Documentation written for Tcl users may look scary and confusing if you are not
used to reading it, but it's not that hard after all. For example, if you want
to change how a :class:`.Label` widget looks, open :man:`ttk_label(3tk)` and
Ctrl+F for whatever you are looking for. Pythotk's documentation contains some
examples that should get you started with writing Pythotk code, but unlike
Pythotk's documentation, the manual pages explain every available feature in
full detail.


Event Loop
----------

Tk is event-based. When you click a :class:`~pythotk.Button`, a click event is
generated, and Tk processes it. Usually that involves making the button look
like it's pressed down, and maybe calling a callback function that you have
told the button to run.

The **event loop** works essentially like this pseudo code::

    while True:
        handle_an_event()
        if there_are_no_more_events_because_we_handled_all_of_them:
            wait_for_more_events()

.. function:: pythotk.run

    This function runs the event loop as shown above until
    :func:`~pythotk.quit` is called.

.. function:: pythotk.quit

    Stop the event loop and destroy all widgets.

    This function calls ``destroy .`` in Tcl, and that's documented in
    :man:`destroy(3tk)`. Note that this function does not tell Python to quit;
    only pythotk quits, so you can do this::

        import pythotk as tk

        window = tk.Window()
        tk.Button(window, "Quit", tk.quit).pack()
        tk.run()
        print("Still alive")

    If you click the button, it interrupts ``tk.run()`` and the print runs.

    .. note::
        Closing a :class:`.Window` with the X button in the corner calls
        ``tk.quit`` by default. If you don't want that, you can prevent it like
        this::

            window.on_delete_window.disconnect(tk.quit)

        See :class:`.Toplevel` for details.
