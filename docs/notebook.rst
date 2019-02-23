.. _notebook:

Notebook Widget
===============

**Manual page:** :man:`ttk_notebook(3tk)`

This widget is useful for creating tabs as in the tabs of your web browser, not
``\t`` characters. Let's look at an example.

::

    import teek

    window = teek.Window("Notebook Example")
    notebook = teek.Notebook(window)
    notebook.pack(fill='both', expand=True)

    for number in [1, 2, 3]:
        label = teek.Label(notebook, "Hello {}!".format(number))
        tab = teek.NotebookTab(label, text="Tab {}".format(number))
        notebook.append(tab)

    window.geometry(300, 200)
    window.on_delete_window.connect(teek.quit)
    teek.run()

This program displays a notebook widget with 3 tabs. Let's go trough some of
the code.

::

    label = teek.Label(notebook, "Hello {}!".format(number))

The label is created as a child widget of the notebook, because it will be
added to the notebook eventually. However, we *don't* use a
:ref:`geometry manager <geometry-managers>` because the notebook itself handles
showing the widget.

::

    tab = teek.NotebookTab(label, text="Tab {}".format(number))

We need to create a :class:`.NotebookTab` object in order to add a tab to the
notebook. The :class:`.NotebookTab` objects themselves are **not** widgets. A
:class:`.NotebookTab` represents a widget and its tab options like ``text``.

::

    notebook.append(tab)

Lists also have an append method, and this is no coincidence.
:class:`.Notebook` widgets behave like lists, and if you can do something to a
list, you can probably do it to a notebook as well. However, there are a few
things you can't do to notebook widgets, but you can do to lists:

* You can't put any objects you want into a :class:`.Notebook`. All the objects
  must be :class:`NotebookTabs <.NotebookTab>`.
* You can't slice notebooks like ``notebook[1:]``. However, you can get a list
  of all tabs in the notebook with ``list(notebook)`` and then slice that.
* You can't sort notebooks like ``notebook.sort()``. However, you can do
  ``sorted(notebook)`` to get a sorted list of
  :class:`NotebookTabs <.NotebookTab>`, except that it doesn't quite work
  because tab objects can't be compared with each other. Something like
  ``sorted(notebook, key=(lambda tab: tab.config['text']))`` might be useful
  though.
* You can't add the same :class:`.NotebookTab` to the notebook twice, and in
  fact, you can't create two :class:`NotebookTabs <.NotebookTab>` that
  represent the same widget, so you can't add the same widget to the notebook
  as two different tabs.

Note that instead of this...

::

    label = teek.Label(notebook, "Hello {}!".format(number))
    tab = teek.NotebookTab(label, text="Tab {}".format(number))
    notebook.append(tab)

...you can also do this::

    notebook.append(
        teek.NotebookTab(
            teek.Label(notebook, "Hello {}!".format(number)),
            text="Tab {}".format(number)
        )
    )

I recommend using common sense here. The first alternative is actually only
half as many lines of code as the second one, even though it uses more
variables. Try to keep the code readable, as usual.

Here is some reference:

.. autoclass:: teek.Notebook
    :members:
.. autoclass:: teek.NotebookTab
    :members:
