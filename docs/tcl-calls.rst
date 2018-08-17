Tcl Calls
=========

.. note::
    This section assumes that you know Tcl. You may have learned some of it
    while using tkinder, but something like
    `Learn Tcl in Y Minutes <https://learnxinyminutes.com/docs/tcl/>`_ might be
    useful for you.

Tkinder does most things by calling commands in Tcl. You can also call Tcl
commands yourself, which is useful if you want to do something that can be done
in Tcl, but there is no other way to do it in tkinder.

There are two functions for doing this:

.. autofunction:: tkinder.eval
.. autofunction:: tkinder.call

Both of these functions are ran so that they have access to Tcl's global
variables, and if they create more variables, they will also be global.

The ``None`` means that the return value is ignored, and ``int`` means that
it's converted to a Python integer. There are more details about these
conversions below.


Data Types
----------

Everything is a string in Tcl. Tkinder converts Python objects to strings and
strings to Python objects for you, but you need to tell tkinder what types of
values you want to get. This section describes how.

.. _python-to-tcl:

Arguments passed to :func:`.call` are handled like this:

    * Strings are passed to Tcl as is.
    * If the argument is None, an empty string is passed to Tcl because Tcl uses an
      empty string in many places where Python uses None.
    * If the argument is a dictionary-like object (more precisely,
      :class:`collections.abc.Mapping`), it is turned into a list of pairs. This is
      because ``{'a': 'b', 'c': 'd'}`` and ``['a', 'b', 'c', 'd']`` are represented
      the same way in Tcl.
    * ``True`` and ``False`` are converted to ``1`` and ``0``, respectively.
    * Integers, floats and other real numbers (:class:`numbers.Real`) are converted
      to strings with ``str()``.
    * If the value has a ``to_tcl()`` method, it's called with no arguments. It
      should return a string that will be passed to Tcl.
    * Anything else is treated as an iterable. Every element of the iterable is
      converted as described here, and the result is a Tcl list.

.. _type-spec:

Tkinder also has **type specifications** for converting from a Tcl object to a
Python object. Here is a list of valid type specifications:

    * ``str`` (that is, literally ``str``, not e.g. ``'hello'``) means that a
      string is returned.
    * ``None`` means that the value will be ignored entirely, and the Python value
      is always None.
    * ``bool`` means that the value is treated as a Tcl boolean. All valid Tcl
      booleans specified in :man:`Tcl_GetBoolean(3tcl)` are supported.
    * ``int``, ``float`` or any other subclass of :class:`numbers.Real` means that
      the value will be converted to that class by first converting to string as if
      ``str`` was used, and then calling the class with the stringed value as an
      argument.
    * If the type specification is a class with a ``from_tcl()`` classmethod, that
      will be called with one argument, the value converted to a string. If the
      stringed value is an empty string, None is returned and ``from_tcl()`` is not
      called.

The type specifications can be also combined in the following ways. These
examples use ``str`` and ``int``, but all other valid specifications work as
well. The return types can be nested arbitrarily; for example,
``[(int, float)]`` means a value like ``[(12, 3.4), (56, 7.8)]``.

    * ``[str]`` means a list of strings, of any length.
    * ``(str, int)`` means a tuple of a string followed by an integer. This allows
      you to create a sequence with different kinds of items in it. For
      example, ``(str, str, str)`` is like ``[str]`` except that it also
      makes sure that the length of the result is 3, and returns a tuple instead of
      a list.
    * ``{str: int}`` means a dictionary with string keys and integer values.

Examples:

>>> tk.call([str], 'list', 'a', 'b', 'c')
['a', 'b', 'c']
>>> tk.call((str, int, float), 'list', 'hello', '3', '3.14')
('hello', 3, 3.14)
>>> tk.call([bool], 'list', 'yes', 'ye', 'true', 't', 'on', '1')
[True, True, True, True, True, True]
>>> tk.call({str: [int]}, 'dict', 'create', 'a', '1', 'b', '2')  # doctest: +SKIP
{'a': [1], 'b': [2]}
>>> tk.call([str], 'list', 123, 3.14, None, 'hello')
['123', '3.14', '', 'hello']

If you are writing a library in tkinder, you may need this function:

.. autofunction:: tkinder.check_type
