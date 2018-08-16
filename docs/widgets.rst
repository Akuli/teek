Widgets
=======

Right now tkinder doesn't have all of the widgets that tkinter has, but many
widgets are implemented.


.. _options:

Options
-------

Widgets take options that change how they look or behave. There are a few
ways to access and change the options:

* Initialization arguments: ``tkinder.Label(window, text="hello")``
  creates a label with the ``text`` option set to ``"hello"``.
* The ``config`` attribute is a dict-like object of options, and you can change
  the text of the label like ``the_label.config['text'] = "new text"``. Note
  that this is different from tkinter where you would instead do
  ``the_label.config(text="new text")`` or ``the_label['text'] = "new text"``;
  in tkinder, you instead always use the ``config`` object.


Widget Reference
----------------

.. autoclass:: tkinder.Widget
    :members:
.. autoclass:: tkinder.Window
    :members:
.. autoclass:: tkinder.Label
    :members:
.. autoclass:: tkinder.Button
    :members:
.. autoclass:: tkinder.Separator
    :members:
.. autoclass:: tkinder.Frame
    :members:
.. autoclass:: tkinder.Toplevel
    :members:
