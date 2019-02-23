Dialogs
=======

.. module:: teek.dialog

This page contains things for asking the user things like file names and
colors. If you want to display a custom dialog, create a :class:`.Window`, add
some stuff to it and use :meth:`~.Toplevel.wait_window`.

.. note::
    All functions documented on this page take a ``parent`` keyword argument.
    Use that whenever you are calling the functions from a program that has
    another window. This way the dialog will look like it belongs to that
    parent window.


Message Boxes
-------------

These functions call :man:`tk_messageBox(3tk)`. Options are passed to
:man:`tk_messageBox(3tk)` so that this code...
::

    teek.dialog.ok_cancel("Question", "Do you want that?")

...does a Tcl call like this:

.. code-block:: tcl

    tk_messageBox -type okcancel -title "Question" -message "Do you want that?" -icon question

.. function:: info(title, message, detail=None, **kwargs)
              warning(title, message, detail=None, **kwargs)
              error(title, message, detail=None, **kwargs)

    Each of these functions shows a message box that has an "ok" button. The
    icon option is ``'info'``, ``'warning'`` or ``'error'`` respectively. These
    functions always return ``None``.

.. function:: ok_cancel(title, message, detail=None, **kwargs)

    Shows a message box with "ok" and "cancel" buttons. The icon is
    ``'question'`` by default, but you can change it by passing a keyword
    argument, e.g. ``icon='warning'``. Returns ``True`` if "ok" is clicked, and
    ``False`` if "cancel" is clicked.

.. function:: retry_cancel(title, message, detail=None, **kwargs)

    Like :func:`ok_cancel`, but with a "retry" button instead of an "ok" button
    and ``'warning'`` as the default icon.

.. function:: yes_no(title, message, detail=None, **kwargs)

    Shows a message box with "yes" and "no" buttons. The icon is ``'question'``
    by default. Returns ``True`` for "yes" and ``False`` for "no".

.. function:: yes_no_cancel(title, message, detail=None, **kwargs)

    Shows a message box with "yes", "no" and "cancel" buttons. The icon is
    ``'question'`` by default. Returns one of the strings ``'yes'``, ``'no'``
    or ``'cancel'``.

.. function:: abort_retry_ignore(title, message, detail=None, **kwargs)

    Like :func:`yes_no_cancel`, but with different buttons and return value
    strings. The icon is ``'error'`` by default.


File and Directory Dialogs
--------------------------

Keyword arguments work as usual. Note that paths are returned as strings of
absolute paths, not e.g. :class:`pathlib.Path` objects.

.. autofunction:: open_file
.. autofunction:: open_multiple_files
.. autofunction:: save_file
.. autofunction:: directory


Other Dialogs
-------------

.. autofunction:: color
