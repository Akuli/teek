.. _widgets:

Widget Reference
================

This is a big list of widgets and explanations of what they do. As usual, don't
try to read all of it, unless you're very bored; it's best to find what you're
looking for, and ignore rest of this.

.. toctree::
    :hidden:

    textwidget
    notebook
    menu

.. autoclass:: pythotk.Widget
    :members: from_tcl, to_tcl, destroy, winfo_exists, winfo_children, winfo_toplevel, winfo_width, winfo_height

.. autoclass:: pythotk.Button
    :members:
.. autoclass:: pythotk.Checkbutton
    :members:
.. autoclass:: pythotk.Entry
    :members:
.. autoclass:: pythotk.Frame
    :members:
.. autoclass:: pythotk.Label
    :members:
.. autoclass:: pythotk.LabelFrame
    :members:

.. class:: pythotk.Menu
    :noindex:

    See :ref:`menu`.

.. class:: pythotk.Notebook
    :noindex:

    See :ref:`notebook`.

.. autoclass:: pythotk.Progressbar
    :members:
.. autoclass:: pythotk.Scrollbar
    :members:
.. autoclass:: pythotk.Separator
    :members:

.. class:: pythotk.Text
    :noindex:

    See :ref:`textwidget`.

.. autoclass:: pythotk.Toplevel
    :members:
.. autoclass:: pythotk.Window
    :members:
