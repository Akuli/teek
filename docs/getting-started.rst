.. _getting-started:

Getting Started with Tkinder
============================

This page shows you some basic things you need to know when programming with
tkinder.


Manual Pages
------------

Tkinder and tkinter are both ways to use Tk in Python. Tk is a library written
for a programming language called Tcl, so the official documentation of most
things is written in Tcl. Tkinter documentation is mostly copy/pasted from
Tcl's documentation, but I don't like copy/pasting stuff, so in tkinder you
will need to read the Tcl documentation yourself. This is a good thing because
copy/pasting would also mean that tkinder documentation is not updated when a
new feature is added to Tk, which is a problem with tkinter's documentation.

To make reading Tcl documentation easier, tkinder's documentation contains
links to Tcl and Tk manual pages, like :man:`after(3tcl)` or
:man:`ttk_label(3tk)`.

Documentation written for Tcl users may look scary and confusing if you are not
used to reading it, but it's not that hard after all. For example, if you want
to change the justification of a label, open :man:`ttk_label(3tk)` and Ctrl+F
for "justify".


Event Loop
----------

Tk is event-based. When you click a :class:`~tkinder.Button`, a click event is
generated, and Tk processes it. Usually that involves making the button look
like it's pressed down, and maybe calling a callback function that you have
told the button to run.

The **event loop** works essentially like this pseudo code::

    while True:
        handle_an_event()
        if there_are_no_more_events_because_we_handled_all_of_them:
            wait_for_more_events()

.. function:: tkinder.run

    This function runs the event loop as shown above until
    :func:`~tkinder.quit` is called.

.. function:: tkinder.quit

    Stop the event loop and destroy all widgets.

    This function calls ``destroy .`` in Tcl, and that's documented in
    :man:`destroy(3tk)`. Note that this function does not tell Python to quit;
    only tkinder quits, so you can do this::

        import tkinder as tk

        window = tk.Window()
        tk.Button(window, "Quit", tk.quit).pack()
        tk.run()
        print("Still alive")

    If you click the button, it interrupts ``tk.run()`` and the print runs.
