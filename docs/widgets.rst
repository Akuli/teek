Widgets
=======

Right now pythotk doesn't have all of the widgets that tkinter has, but many
widgets are implemented.


.. _options:

Options
-------

Widgets take options that change how they look or behave. There are a few
ways to access and change the options:

* Initialization arguments: ``pythotk.Label(window, text="hello")``
  creates a label with the ``text`` option set to ``"hello"``.
* The ``config`` attribute is a dict-like object of options, and you can change
  the text of the label like ``the_label.config['text'] = "new text"``. Note
  that this is different from tkinter where you would instead do
  ``the_label.config(text="new text")`` or ``the_label['text'] = "new text"``;
  in pythotk, you instead always use the ``config`` object.


Widget Reference
----------------

.. autoclass:: pythotk.Widget
    :members:
.. autoclass:: pythotk.Window
    :members:
.. autoclass:: pythotk.Label
    :members:
.. autoclass:: pythotk.Button
    :members:
.. autoclass:: pythotk.Separator
    :members:
.. autoclass:: pythotk.Frame
    :members:
.. autoclass:: pythotk.Toplevel
    :members:
