Extras
======

.. module:: teek.extras

Big tkinter projects often have their own implementations of some commonly
needed things that tkinter doesn't come with. The ``teek.extras`` module
contains a collection of them.

To use the extras, ``import teek as tk`` is not enough; that doesn't import
any extras. This is good because most teek programs don't need the extras,
and for them, ``import teek as tk`` may run a little bit faster if it
doesn't import the extras. Instead, you typically need to do something like
this to use the extras::

    import teek as tk
    from teek.extras import tooltips

    # now some code that uses tooltips.set_tooltip


.. module:: teek.extras.tooltips

tooltips
--------

This module contains a simple tooltip implementation with teek.

If you have read some of IDLE's source code (if you haven't, that's
good; IDLE's source code is ugly), you might be wondering what this
thing has to do with ``idlelib/tooltip.py``. Don't worry, I didn't
copy/paste any code from idlelib and I didn't read idlelib while I
wrote the tooltip code! Idlelib is awful and I don't want to use
anything from it in my projects.

.. autofunction:: set_tooltip


.. module:: teek.extras.cross_platform

cross_platform
--------------

Most teek things work the same on most platforms, but not everything does.
For example, binding ``<Tab>`` works everywhere, but binding ``<Shift-Tab>``
doesn't work on Linux and you need a different binding instead. This extra
module contains utilities for dealing with things like that.

.. autofunction:: bind_tab_key


.. module:: teek.extras.more_dialogs

more_dialogs
------------

This is useful when :mod:`teek.dialog` is not enough.

All of the functions take these arguments:

* ``title`` will be the title of the dialog.
* ``text`` will be displayed in a label above the text entry or spinbox.
* ``initial_value`` will be added to the entry or spinbox before the user
  changes it.
* ``parent`` is a window widget that the dialog will be displayed on top of.

.. autofunction:: ask_string
.. autofunction:: ask_integer


.. module:: teek.extras.links

links
-----

With this extra, you can insert web browser style links to
:class:`~teek.Text` widgets. This is based on
`this tutorial <http://effbot.org/zone/tkinter-text-hyperlink.htm>`_ that is
almost as old as I am, but it's still usable.

.. autofunction:: add_url_link
.. autofunction:: add_function_link
