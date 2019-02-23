.. _geometry-managers:

Geometry Managers: pack, grid, place
====================================

Geometry managers are ways to add widgets inside other widgets. For example,
``pack`` is a geometry manager. This page contains more information about pack
and two other geometry managers.


Pack
----

This is a simple geometry manager useful for laying out big things. If you want
to have two big widgets next to each other, this is the right choice.

.. seealso::
    There is a beginner-friendly introduction to pack
    :ref:`here <pack-with-frames>`.

Pack options have a ``-`` in front of them in Tcl, but teek hides that, so
Tcl code like ``-anchor center`` looks like ``anchor='center'`` in teek.

Teek widgets have these methods:

.. method:: teek.Widget.pack(**kwargs)

    Search for ``pack configure`` in :man:`pack(3tk)` for details. If you want
    to use the ``-in`` option, you can't do ``widget1.pack(in=widget2)``
    because ``in`` is a reserved keyword in Python and you get a syntax error,
    but teek lets you do ``widget1.pack(in_=widget2)`` instead.

.. method:: teek.Widget.pack_forget()

    See ``pack forget`` in :man:`pack(3tk)`.

.. method:: teek.Widget.pack_info()

    This returns the keyword arguments passed to :meth:`~.Widget.pack` with
    string keys. The types of values are as follows:

    * The value of ``'in'`` is a teek widget.
    * The value of ``'expand'`` is True or False.
    * The values of ``'ipadx'`` and ``'ipady'`` are :class:`.ScreenDistance`
      objects.
    * The values of ``'padx'`` and ``'pady'`` are lists of
      :class:`.ScreenDistance` objects. Each list contains 1 or 2 items; see
      ``-padx`` in :man:`pack(3tk)` for details.
    * Other values are strings.

    See also ``pack info`` in :man:`pack(3tk)`. The returned dictionary is a
    valid ``kwargs`` dict for :meth:`~.Widget.pack`, so you can do this::

        pack_info = widget.pack_info()
        widget.pack_forget()
        ...do something...
        widget.pack(**pack_info)

.. method:: teek.Widget.pack_slaves()

    Returns a list of other :class:`Widgets <.Widget>` packed into the widget.
    See ``pack slaves`` in :man:`pack(3tk)` for more details.


Grid
----

This geometry manager is useful for making griddy things that would be hard or
impossible to do with pack. Here is an example::

    import teek


    window = teek.Window("Calculator")

    rows = [
        ['7', '8', '9', '*', '/'],
        ['4', '5', '6', '+', '-'],
        ['1', '2', '3', None, None],
        [None, None, '.', None, None],
    ]

    for row_number, row in enumerate(rows):
        for column_number, text in enumerate(row):
            if text is not None:
                button = teek.Button(window, text, width=3)
                button.grid(row=row_number, column=column_number, sticky='nswe')

    zerobutton = teek.Button(window, '0')
    zerobutton.grid(row=3, column=0, columnspan=2, sticky='nswe')
    equalbutton = teek.Button(window, '=')
    equalbutton.grid(row=2, column=3, rowspan=2, columnspan=2, sticky='nswe')

    for row_or_column in (window.grid_rows + window.grid_columns):
        row_or_column.config['weight'] = 1

    window.on_delete_window.connect(teek.quit)
    teek.run()

Let's go through some of that line by line.
::

    for row_number, row in enumerate(rows):
        for column_number, text in enumerate(row):

This is a way to loop over the row list with indexes. For example, if ``text``
is ``'*'``, then ``row_number`` is 0 and ``column_number`` is 3, because
``text`` is the fourth element of the first sublist of ``rows``.
::

    button.grid(row=row_number, column=column_number, sticky='nswe')

The ``sticky='nswe'`` makes the button fill all the space it has in the grid
cell. The ``n`` means "north" (up), ``w`` means "west" (left), etc.
::

    zerobutton.grid(row=3, column=0, columnspan=2, sticky='nswe')

``columnspan=2`` makes the button *span* two columns, so some of it is in one
column, and rest of it is in the other. The default is ``columnspan=1``.
::

    for row_or_column in (window.grid_rows + window.grid_columns):
        row_or_column.config['weight'] = 1

This loops through all grid rows and columns of the widget, and makes
everything stretch as the window is resized. Comment out these lines and resize
the window to understand why I did this. See :ref:`grid-row-column-objects`
below for details.


.. method:: teek.Widget.grid(**kwargs)

    Very similar to :meth:`~.Widget.pack`. See ``grid configure`` in
    :man:`grid(3tk)` for details.

.. method:: teek.Widget.grid_forget()

    See ``grid forget`` in :man:`grid(3tk)`.

.. method:: teek.Widget.grid_info()

    Very similar to :meth:`~.Widget.pack_info`. The types of values are as
    follows:

    * The value of ``'in'`` is a teek widget.
    * The values of ``'ipadx'`` and ``'ipady'`` are :class:`.ScreenDistance`
      objects.
    * The values of ``'padx'`` and ``'pady'`` are lists of
      :class:`.ScreenDistance` objects. Each list contains 1 or 2 items; see
      ``-padx`` in :man:`pack(3tk)` for details.
    * The values of ``'row'``, ``'rowspan'``, ``'column'`` and ``'columnspan'``
      are integers.
    * Other values are strings.

.. method:: teek.Widget.grid_slaves()

    Similar to :meth:`~.Widget.pack_slaves`. Use
    :meth:`row_or_column.get_slaves()` if you need the ``-row`` and ``-column``
    options of ``grid slaves`` in :man:`grid(3tk)`.

.. attribute:: teek.Widget.grid_rows
               teek.Widget.grid_columns

    Lists of :ref:`row objects or column objects <grid-row-column-objects>`.


.. _grid-row-column-objects:

Grid Row and Column Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tk has some options and other things that can be done to rows or columns of a
grid. These are represented with row objects and column objects in teek.

>>> window = teek.Window()
>>> window.grid_rows
[]
>>> teek.Label(window, "label text").grid()    # goes to row 0, column 0
>>> window.grid_rows
[<grid row 0: has a config attribute and a get_slaves() method>]
>>> window.grid_columns
[<grid column 0: has a config attribute and a get_slaves() method>]
>>> window.grid_columns[0].config['weight']
0.0
>>> window.grid_columns[0].get_slaves()
[<teek.Label widget: text='label text'>]

Here is the reference:

.. attribute:: row_or_column.config

    An object that represents row or column options. Similar to
    :attr:`.Widget.config`.

    See ``grid columnconfigure`` and ``grid rowconfigure`` in :man:`grid(3tk)`
    for the available options. ``'weight'`` is a float, ``'minsize'`` and
    ``'pad'`` are :class:`.ScreenDistance` objects and ``'uniform'`` is a
    string.

.. method:: row_or_column.get_slaves()

    Returns a list of widgets in the row or column.

    This calls ``grid slaves`` documented in :man:`grid(3tk)` with a ``-row``
    or ``-column`` option.


Place
-----

This geometry manager is useful for placing things relatively. For example,
this puts a button right in the middle of its parent widget::

    button.place(relx=0.5, rely=0.5, anchor='center')

Here ``relx`` and ``rely`` mean "relative x" and "relative y"; that is, values
between 0 and 1. The ``anchor='center'`` says that the center of the *button*
goes to the position given with ``relx`` and ``rely``.

Place can be also used with absolute positions given in pixels:
::

    # 100 pixels down and 200 right from top left corner of the parent widget
    button.place(x=100, y=200)

Usually that's a **bad idea**. 100 pixels on your screen might look different
than 100 pixels on someone else's screen if that other system happens to use
bigger fonts or something else like that. However, placing with pixels can be
useful when working with other things that use pixels. For example, if you
:ref:`bind <binding>` some mouse stuff and the user clicks something, you get
the mouse x and y coordinates in pixels.


.. method:: teek.Widget.place(**kwargs)

    See ``place configure`` in :man:`place(3tk)` for details. This is similar
    to :meth:`~.Widget.pack`.

.. method:: teek.Widget.place_forget()

    See ``place forget`` in :man:`place(3tk)`.

.. method:: teek.Widget.place_info()

    Very similar to :meth:`~.Widget.pack_info` and :meth:`~.Widget.grid_info`.
    The types of values are as follows:

    * The value of ``'in'`` is a teek widget.
    * The values of ``'width'``, ``'height'``, ``'x'`` and ``'y'`` are
      :class:`.ScreenDistance` objects.
    * The values of ``'relwidth'``, ``'relheight'``, ``'relx'`` and ``'rely'``
      are floats.
    * Other values are strings.

    See also ``place info`` in :man:`place(3tk)`.

.. method:: teek.Widget.place_slaves()

    Returns a list of other :class:`Widgets <.Widget>` placed into the widget.
