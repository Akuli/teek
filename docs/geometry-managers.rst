Geometry Managers: pack, grid, place
====================================

Geometry managers are ways to add widgets inside other widgets.

.. note::
    Right now :man:`pack(3tk)` is the only supported geometry manager, and you
    need to do :ref:`Tcl calls <tcl-calls>` yourself if you want to use
    :man:`grid(3tk)` or :man:`place(3tk)`. I know, it sucks :(


Pack
----

This is a simple geometry manager useful for laying out big things. If you want
to have two big widgets next to each other, this is the right choice.

Pack options have a ``-`` in front of them in Tcl, but pythotk hides that, so
Tcl code like ``-anchor center`` looks like ``anchor='center'`` in pythotk.

Pythotk widgets have these methods:

.. method:: Widget.pack(**kwargs)

    Search for ``pack configure`` in :man:`pack(3tk)` for details. If you want
    to use the ``-in`` option, you can't do ``widget1.pack(in=widget2)``
    because ``in`` is a reserved keyword in Python and you get a syntax error,
    but pythotk lets you do ``widget1.pack(in_=widget2)`` instead.

.. method:: Widget.pack_forget()

    See ``pack forget`` in :man:`pack(3tk)`.

.. method:: Widget.pack_info()

    This returns the keyword arguments passed to :meth:`~Widget.pack` with
    string keys. The types of values are as follows:

    * The value of ``'in'`` is a pythotk widget.
    * The value of ``'expand'`` is True or False.
    * Other values are strings.

    See also ``pack info`` in :man:`pack(3tk)`. The returned dictionary is a
    valid ``kwargs`` dict for :meth:`~.Widget.pack`, so you can do this::

        pack_info = widget.pack_info()
        widget.pack_forget()
        ...do something...
        widget.pack(**pack_info)

.. method:: Widget.pack_slaves()

    Returns a list of other :class:`Widgets <.Widget>` packed into the widget.
    See ``pack slaves`` in :man:`pack(3tk)` for more details.
