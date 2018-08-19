.. _textwidget:

Text Widget
===========

**Manual page:** :man:`text(3tk)`

This widget is useful for displaying text that the user should be able to edit.
The text can contain multiple lines. Use :class:`.Entry` if the text is just 1
line, or :class:`.Label` if you don't want the user to be able to edit the
text.

.. note::
    This widget is **not** a Ttk widget because there is no Ttk text widget.
    However, that's not a problem because usually text widgets are configured
    to have custom colors anyway instead of using the Ttk theme's colors. For
    example, `my editor <https://github.com/Akuli/porcupine>`_ lets the user
    change the colors of the text widget by selecting a color theme from a
    menu. Only the text widget colors change, and Ttk widgets are not affected
    by that.


Hello World!
------------

::

    import pythotk as tk

    window = tk.Window()
    text = tk.Text(window)
    text.pack()
    text.insert(text.start, 'Hello World!')

    tk.run()

This program displays a window with a ``Hello World!`` text in it displayed
using a monospace font. It lets you edit the text.


.. _textwidget-index:

Index Objects
-------------

..  this uses :any:`namedtuple` instead of :func:`namedtuple` because any
    shows it as "namedtuple", not "namedtuple()"

In the above example, we used :meth:`.Text.insert`, and we told it to insert
the hello world to the beginning of the text widget by passing it
``text.start``. Here ``text.start`` was a text index
:any:`namedtuple <collections.namedtuple>`:

>>> window = tk.Window()
>>> text = tk.Text(window)
>>> text.start
TextIndex(line=1, column=0)

.. note::
    Line numbers start at 1, and columns start at 0. Tk does this too, and
    pythotk doesn't hide it because it is very common to call the first line
    "line 1"...

    .. code-block:: py3tb

        Traceback (most recent call last):
          File "my_file.py", line 1, in <module>
            first line of code
          ...

    ...but it's just as common to start column numbering at 0, just like string
    indices.

    Avoid working with 0-based line numbers if you can. That way your pythotk
    code will be simpler and less confusing.

The text indices can do everything that namedtuples can do.

>>> text.start.line     # do this if you need only line or column
1
>>> text.start.column
0
>>> line, column = text.start       # do this if you need both
>>> line
1
>>> column
0

In general, they behave like tuples:

>>> for lol in text.start:
...     print(lol)
...
1
0
>>> list(text.start)
[1, 0]

There is also ``text.end``, which is the text index of the end of the text
widget:

>>> text.end
TextIndex(line=1, column=0)
>>> text.end == text.start      # there's nothing in this text widget yet
True
>>> text.insert(text.start, 'hello')
>>> text.end
TextIndex(line=1, column=5)
>>> text.end == text.start
False
>>> text.insert(text.end, '\nsome text')    # now there are 2 lines of text
>>> text.end
TextIndex(line=2, column=9)
>>> print(text.get(text.start, text.end))
hello
some text

Text indices have the following attributes and methods:

.. method:: some_text_index.forward(chars=0, indices=0, lines=0)

    Return a new text index after this index (or before, if the arguments are
    negative, or the same index if all arguments are zero). All arguments must
    be integers, and given as keyword arguments. Search for ``+ count`` in
    :man:`text(3tk)` for an explanation of what each argument does.

    >>> text.get(text.start, text.end)
    'hello\nsome text'
    >>> text.start.forward(chars=3)
    TextIndex(line=1, column=3)
    >>> text.start.forward(chars=7)       # goes over a newline character
    TextIndex(line=2, column=1)
    >>> text.start.forward(chars=1000)    # won't go past end of text widget
    TextIndex(line=2, column=9)

.. method:: some_text_index.back(chars=0, indices=0, lines=0)

    Like :meth:`forward`, but goes back instead of forward.

.. method:: some_text_index.linestart()
.. method:: some_text_index.lineend()
.. method:: some_text_index.wordstart()
.. method:: some_text_index.wordend()

    These return new text indices. Search for e.g. ``linestart`` in
    :man:`text(3tk)` for details.

.. method:: some_text_index.to_tcl()

    Returns a ``'line.column'`` string. See :ref:`to-tcl`.

.. tip::
    Text indices are usually namedtuples, but methods that take text indices as
    arguments (e.g. :meth:`~.Text.insert`) can also take regular
    ``(line, column)`` tuples. You can use :meth:`~.Text.index` to create new
    text index namedtuples from line and column numbers.


.. _textwidget-marks:

Marks
-----

If you have a text widget that contains ``hello world``, the position just
before ``w`` changes if you change ``hello`` to something else, or if the user
edits the text widget's content:

>>> text.replace(text.start, text.end, "hello world")
>>> text.get(text.start, text.end)
'hello world'
>>> before_w = text.index(1, 6)
>>> before_w
TextIndex(line=1, column=6)
>>> text.get(before_w, text.end)
'world'
>>> text.replace(text.start, text.start.forward(chars=5), 'hi')
>>> text.get(text.start, text.end)      # hello was replaced with hi
'hi world'
>>> text.get(before_w, text.end)        # but before_w didn't update!
'ld'
>>> before_w
TextIndex(line=1, column=6)

We can solve this problem by adding a **mark**:

>>> text.replace(text.start, text.end, "hello world")
>>> text.marks['before_w'] = text.index(1, 6)
>>> text.get(text.marks['before_w'], text.end)
'world'
>>> text.replace(text.start, text.start.forward(chars=5), 'hi')
>>> text.get(text.marks['before_w'], text.end)
'world'
>>> text.get(text.start, text.end)
'hi world'

Marks move with the text as the text before them is changed.
:attr:`.Text.marks` is a dictionary-like object with mark name strings as keys
and :ref:`index objects <textwidget-index>` as values. There is also a special
``'insert'`` mark that represents the cursor position::

    # move cursor to new_cursor_pos
    text.marks['insert'] = new_cursor_pos

There are more details about marks in the ``MARKS`` section of
:man:`text(3tk)`.


Tags
----

You can use tags to change things like color of *some* of the text without
changing all of it. For example, this code displays a ``Hello World`` with a
red ``Hello`` and a green ``World``::

    import pythotk as tk


    window = tk.Window("Text Widget Demo")

    text = tk.Text(window)
    text.pack(fill='both', expand=True)
    text.insert(text.start, "hello world")

    hello_tag = text.get_tag('hello_tag')
    hello_tag['foreground'] = tk.Color('red')
    hello_tag.add(text.start, text.start.forward(chars=len('hello')))

    world_tag = text.get_tag('world_tag')
    world_tag['foreground'] = tk.Color('green')
    world_tag.add(text.end.back(chars=len('world')), text.end)

    tk.run()

Each tag has a name which is mostly useful for debugging. If you want to create
a tag, call :meth:`~.Text.get_tag` with whatever name you want; a new tag is
created if a tag with the given name doesn't exist yet.

>>> text.get_tag('hello_tag')
<Text widget tag 'hello_tag'>

Tag objects behave like :attr:`~.Widget.config` objects, so you can e.g. change
their options with their dictionary-like behaviour. See ``TAGS`` in
:man:`text(3tk)` for a list of supported options. As usual, the options are
given without a leading ``-``, like ``'foreground'`` instead of
``'-foreground'``.

Tag objects have these attributes and methods. Search for ``pathName tag`` in
:man:`text(3tk)` for more information about them.

.. attribute:: some_tag.name

    The Tk name of the tag, as a string.

.. method:: some_tag.add(index1, index2)

    Add this tag to text between the given :ref:`indices <textwidget-index>`.

.. method:: some_tag.delete()

    Remove this tag from everywhere in the text widget, and forget all
    configuration options the tag has been given.

    .. note:: :meth:`delete` and :meth:`remove` do different things.

.. method:: some_tag.remove(index1=None, index2=None)

    Remove this tag from the text widget between the given
    :ref:`indices <textwidget-index>`. ``index1`` defaults to
    :attr:`~.Text.start`, and ``index2`` defaults to :attr:`~.Text.end`.

.. method:: some_tag.to_tcl()

    Returns :attr:`some_tag.name`. See :ref:`to-tcl`.

.. method:: some_tag.ranges()

    Returns a list of ``(start_index, end_index)`` pairs that describe where
    the tag has been added. The indexes are
    :ref:`index objects <textwidget-index>`.

.. method:: some_tag.prevrange(index1, index2=None)
.. method:: some_tag.nextrange(index1, index2=None)

    These return the previous or next ``(start_index, end_index)`` pair. See
    :meth:`ranges` and :man:`text(3tk)`.


Text Widget Methods and Attributes
----------------------------------

.. autoclass:: pythotk.Text
    :members:
