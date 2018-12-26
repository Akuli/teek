Extras
======

.. module:: pythotk.extras

Big tkinter projects often have their own implementations of some commonly
needed things that tkinter doesn't come with. The ``pythotk.extras`` module
contains a collection of them.

To use the extras, ``import pythotk as tk`` is not enough; that doesn't import
any extras. This is good because most pythotk programs don't need the extras,
and for them, ``import pythotk as tk`` may run a little bit faster if it
doesn't import the extras. Instead, you typically need to do something like
this to use the extras::

    import pythotk as tk
    from pythotk.extras import tooltips

    # now some code that uses tooltips.set_tooltip


.. module:: pythotk.extras.tooltips

tooltips
--------

This module contains a simple tooltip implementation with pythotk.

If you have read some of IDLE's source code (if you haven't, that's
good; IDLE's source code is ugly), you might be wondering what this
thing has to do with ``idlelib/tooltip.py``. Don't worry, I didn't
copy/paste any code from idlelib and I didn't read idlelib while I
wrote the tooltip code! Idlelib is awful and I don't want to use
anything from it in my projects.

.. autofunction:: set_tooltip


.. module:: pythotk.extras.cross_platform

cross_platform
--------------

Most pythotk things work the same on most platforms, but not everything does.
For example, binding ``<Tab>`` works everywhere, but binding ``<Shift-Tab>``
doesn't work on Linux and you need a different binding instead. This extra
module contains utilities for dealing with things like that.

.. autofunction:: bind_tab_key


.. module:: pythotk.extras.more_dialogs

more_dialogs
------------

This is useful when :mod:`pythotk.dialog` is not enough.

All of the functions take these arguments:

* ``title`` will be the title of the dialog.
* ``text`` will be displayed in a label above the text entry or spinbox.
* ``initial_value`` will be added to the entry or spinbox before the user
  changes it.
* ``parent`` is a window widget that the dialog will be displayed on top of.

.. autofunction:: ask_string
.. autofunction:: ask_integer
