.. _getting-started:

Getting Started with Tkinder
============================

This page contains things you need to know when programming with tkinder.


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
