Miscellaneous Classes
=====================

This page contains documentation of classes that represent different kinds of
things.


Colors
------

.. autoclass:: teek.Color
    :members:


Callbacks
---------

.. autoclass:: teek.Callback
    :members:


.. _font-objs:

Fonts
-----

There are different kinds of fonts in Tk:

* **Named fonts** are mutable; if you set the font of a widget to a named font
  and you then change that named font (e.g. make it bigger), the widget's font
  will change as well.
* **Anonymous fonts** don't work like that, but they are handy if you don't
  want to create a font object just to set the font of a widget.

For example, if you have :class:`.Label`...

>>> window = teek.Window()
>>> label = teek.Label(window, "Hello World")
>>> label.pack()

...and you want to make its text bigger, you can do this::

>>> label.config['font'] = ('Helvetica', 20)

This form is the teek equivalent of the alternative ``[3]`` in the
``FONT DESCRIPTIONS`` part of :man:`font(3tk)`. All of the other font
descriptions work as well.

If you then get the font of the label, you get a :class:`teek.Font` object:

>>> label.config['font']
Font('Helvetica 20')

With a named font, the code looks like this:

>>> named_font = teek.NamedFont(family='Helvetica', size=20)
>>> label.config['font'] = named_font
>>> named_font.size = 50    # even bigger! label will use this new size automatically

Of course, :class:`.Font` and :class:`.NamedFont` objects can also be set to
``label.config['font']``.

.. autoclass:: teek.Font
    :members:

.. autoclass:: teek.NamedFont
    :members:


Tcl Variable Objects
--------------------

.. autoclass:: teek.TclVariable
    :members:

.. class:: teek.StringVar
           teek.IntVar
           teek.FloatVar
           teek.BooleanVar

    Handy :class:`.TclVariable` subclasses for variables with :class:`str`,
    :class:`int`, :class:`float` and :class:`bool` values, respectively.


Images
------

.. autoclass:: teek.Image
    :members:


Screen Distance Objects
-----------------------

.. autoclass:: teek.ScreenDistance
    :members:
