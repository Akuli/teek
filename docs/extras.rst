Extras
======

.. module:: pythotk.extras

Big tkinter projects often have their own implementations of some commonly
needed things that tkinter doesn't come with. The ``pythotk.extras`` module
contains a collection of them. To use it, you don't need to import anything
special; you can just ``import pythotk as tk`` as usual, and then use e.g.
``tk.extras.set_tooltip``.

.. autofunction:: pythotk.extras.set_tooltip
.. autofunction:: pythotk.extras.bind_tab_key
