.. _canvaswidget:

Canvas Widget
=============

**Manual page:** :man:`canvas(3tk)`

This widget is useful for displaying drawings and other things. See
:source:`examples/paint.py` for an example.

.. note::
    This widget is **not** a Ttk widget because there is no Ttk canvas widget.
    However, that's not a problem because usually canvas widgets contain
    things that shouldn't be colored based on the current Ttk theme anyway.


Hello World!
------------

This program displays some simple things on a canvas.

::

    import teek

    window = teek.Window()
    canvas = teek.Canvas(window)
    canvas.pack()

    canvas.create_line(100, 100, 120, 150)
    canvas.create_oval(200, 200, 250, 250)
    canvas.create_rectangle(200, 100, 230, 130)

    window.on_delete_window.connect(teek.quit)
    teek.run()

The background color of the canvas depends on the system that this
code is ran on. If you don't want that, you can create the canvas like
``canvas = teek.Canvas(window, bg='white')``, for instance.

The numbers passed to :func:`~teek.Canvas.create_line` and similar methods are
**coordinates**. They work so that, for example, ``(200, 100)`` means 200 pixels
right from the left side of the canvas, and 100 pixels down from the top. The
"how much right" coordinate is called the **x coordinate**, and the "how much
down" coordinate is called the "y coordinate".

.. note::
    The y coordinates work differently than they usually work in mathematics;
    that is, more y means down in Tk and teek. This also means that rotations
    go the other way, and positive angles mean clockwise rotations in teek even
    though they mean counter-clockwise rotations in mathematics.

The ``create_something()`` methods take four numbers each, because they are two
pairs of ``(x, y)`` coordinates. For example,
``canvas.create_rectangle(200, 100, 230, 130)`` means that one corner of the
created rectangle is at ``(200, 100)`` and another corner is at ``(230, 130)``.
(It is actually a square, because it is 30 pixels high and 30 pixels wide).


.. _canvas-items:

Item Objects
------------

The ``create_something()`` methods return item objects that you can keep around
and do stuff with. For example, you can do this::

    >>> canvas = teek.Canvas(teek.Window())
    >>> square = canvas.create_rectangle(200, 100, 230, 130)
    >>> square
    <rectangle canvas item at (200.0, 100.0, 230.0, 130.0)>
    >>> square.config['fill'] = 'red'       # this makes the square red

Or you can pass some config options to ``create_rectangle()`` directly, as
usual::

    >>> square = canvas.create_rectangle(200, 100, 230, 130, fill='red')
    >>> square.config['fill']
    <Color 'red': red=255, green=0, blue=0>

Here ``square`` is a canvas item object.

All canvas item objects have these attributes and methods:

.. attribute:: some_canvas_item.config

    This dictionary-like object is similar to the ``config`` attribute of
    widgets, which is explained :ref:`here <options>`.

.. attribute:: some_canvas_item.coords

    A tuple of coordinates of the canvas. This can be set to move an existing
    canvas item without having to create a new item.

.. attribute:: some_canvas_item.tags

    This is a set-like object of the canvas item's :ref:`tags <canvas-tags>`,
    as strings. You can ``.add()`` and ``.remove()`` the tags, for example.

.. attribute:: some_canvas_item.item_type_name

    The kind of the canvas item as a string, e.g. ``'oval'`` or ``'rectangle'``.

.. method:: some_canvas_item.delete()

    This deletes the canvas item. Trying to do something with the canvas item
    will raise an error.
    ::

        >>> circle = canvas.create_oval(200, 200, 250, 250)
        >>> circle
        <oval canvas item at (200.0, 200.0, 250.0, 250.0)>
        >>> circle.delete()
        >>> circle
        <deleted oval canvas item>

.. method:: some_canvas_item.find_above()
            some_canvas_item.find_below()

    These return another canvas item object. See ``pathName find`` and the
    ``above`` and ``below`` parts of ``pathName addtag`` in :man:`canvas(3tk)`
    for more information.

The type of the canvas items is accessible as ``the_canvas_widget.Item``. It's
useful for :func:`isinstance` checks, but not much else::

    >>> isinstance(circle, canvas.Item)
    True
    >>> isinstance('lolwat', canvas.Item)
    False

Note that this is different for each canvas; the items of two different
canvases are not of the same type.


.. _canvas-tags:

Tags
----

If you have lots of related canvas items, you can just keep a list of them and
do something to each item in that list. Alternatively, you can use tags to mark
the canvas items, and then do something to all items tagged with a specific
tag. Like this::

    >>> canvas = teek.Canvas(teek.Window())
    >>> line = canvas.create_line(100, 100, 120, 150)
    >>> circle = canvas.create_oval(200, 200, 250, 250)
    >>> square = canvas.create_rectangle(200, 100, 230, 130)
    >>> canvas.find_withtag('lol')
    []
    >>> circle.tags.add('lol')
    >>> canvas.find_withtag('lol')   # returns a list that contains the circle
    [<oval canvas item at (200.0, 200.0, 250.0, 250.0)>]


Canvas Widget Methods and Attributes
------------------------------------

.. autoclass:: teek.Canvas
    :members:
