Platform Information
====================

This page documents things that can tell you which platform your program is
running on.

.. data:: teek.TCL_VERSION
          teek.TK_VERSION

    These can be used for checking the versions of the Tcl interpreter and its
    Tk library that teek is using. These are two-tuples of integers, and you
    can compare integer tuples nicely, so you can do e.g. this::

        if teek.TK_VERSION >= (8, 6):
            # use a feature new in Tk 8.6
        else:
            # show an error message or do things without the new feature

    Teek refuses to run if Tcl or Tk is older than 8.5, so you can use all
    features new in Tcl/Tk 8.5 freely.

    .. note::
        The manual page links in this tutorial like :man:`label(3tk)` always
        point to the latest manual pages, which are for Tcl/Tk 8.6 at the time
        of writing this.

.. autofunction:: teek.windowingsystem

    This function returns ``'win32'``, ``'aqua'`` or ``'x11'``. Use it instead
    of :func:`platform.system` when you have platform-specific teek code.
    For example, it's possible to run X11 on a Mac, in which case
    :func:`platform.system` returns ``'Darwin'`` and this function returns
    ``'x11'``. If you have code that should even then behave like it would
    normally behave on a Mac, use :func:`platform.system`.

    The Tk documentation for this function is ``tk windowingsystem`` in
    :man:`tk(3tk)`.
