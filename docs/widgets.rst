.. _widgets:

Widget Reference
================

Right now pythotk doesn't have all of the widgets that tkinter has, but many
widgets are implemented.

.. note::
    Some widgets are not documented here; instead, there are separate pages
    about them because there are so many things to talk about. Here is a list
    of these widgets:

    .. toctree::
        :maxdepth: 1

        Text <textwidget>


.. autoclass:: pythotk.Widget
    :members: from_tcl, to_tcl, destroy, winfo_exists, winfo_children, winfo_toplevel
.. autoclass:: pythotk.Window
    :members:
.. autoclass:: pythotk.Button
    :members:
.. autoclass:: pythotk.Label
    :members:
.. autoclass:: pythotk.Entry
    :members:
.. autoclass:: pythotk.Separator
    :members:
.. autoclass:: pythotk.Frame
    :members:
.. autoclass:: pythotk.Toplevel
    :members:
