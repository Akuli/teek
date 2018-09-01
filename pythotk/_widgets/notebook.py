import collections.abc
import contextlib

import pythotk as tk
from pythotk._structures import ConfigDict
from pythotk._tcl_calls import needs_main_thread
from pythotk._widgets.base import ChildMixin, Widget


class TabConfigDict(ConfigDict):

    def __init__(self, tab):
        self._tab = tab
        super().__init__()
        self._types.update({
            'state': str,
            'sticky': str,
            'padding': [tk.ScreenDistance],
            'text': str,
            'image': tk.Image,
            'compound': str,
            'underline': int,
        })

    def _set(self, option, value):
        self._tab._check_in_notebook()
        tk.tcl_call(None, self._tab.notebook,
                    'tab', self.widget, '-' + option, value)

    def _get(self, option):
        self._tab._check_in_notebook()
        return tk.tcl_call(self._types[option], self._tab.notebook,
                           'tab', self._tab.widget, '-' + option)

    def _list_options(self):
        return tk.tcl_call({}, self._tab.notebook,
                           'tab', self._tab.widget).keys()


class NotebookTab:
    """
    Represents a tab that is in a notebook, or is ready to be added to a
    notebook.

    ``NotebookTab`` objects are **not** widgets; they represent a widget in the
    notebook and the notebook tab options associated with that widget, like the
    text of the tab. The *widget* will show up in the tab when the tab is added
    to a notebook.

    Most methods raise :exc:`RuntimeError` if the tab has not been added to a
    notebook yet. This includes doing pretty much anything with :attr:`config`.

    For convenience, options can be passed when creating a
    :class:`.NotebookTab`, so that this...
    ::

        notebook.append(tk.NotebookTab(some_widget, text="Tab Title"))

    ...does the same thing as this::

        tab = tk.NotebookTab(some_widget, text="Tab Title")
        notebook.append(tab)
        tab.config['text'] = "Tab Title"

    .. attribute:: config

        Similar to the ``config`` attribute that widgets have. The available
        options are documented as ``TAB OPTIONS`` in :man:`ttk_notebook(3tk)`.

    .. attribute:: widget

        This attribute and initialization argument is the widget in the tab. It
        should be a child widget of the notebook.

    .. attribute:: notebook

        The :class:`.Notebook` widget that the tab is in, or None. Don't set
        this attribute yourself; instead, add the tab to a :class:`.Notebook`
        or remove it from the notebook. This attribute will update
        automatically.
    """

    def __init__(self, widget, **kwargs):
        self.widget = widget
        self.notebook = None
        self.config = TabConfigDict(self)
        self._initial_options = kwargs

    # only used in Notebook.__getitem__, which is important because overriding
    # Notebook.__getitem__ for custom tab classes is a documented thing to do
    @classmethod
    def _from_notebook_and_widget(cls, notebook, widget):
        tab = cls.__new__(cls)   # create new instance without __init__ call
        tab.notebook = notebook
        tab.widget = widget
        tab.config = TabConfigDict(tab)
        tab._initial_options = {}
        return tab

    def __eq__(self, other):
        if not isinstance(other, NotebookTab):
            return NotImplemented
        return self.widget is other.widget and self.notebook is other.notebook

    def __hash__(self):
        return hash((self.widget, self.notebook))

    def _check_in_notebook(self):
        if self.notebook is None:
            raise RuntimeError("the tab is not in a notebook yet")

    @contextlib.contextmanager
    def _adding_to_notebook_helper(self, notebook):
        if self.notebook is not None:
            raise RuntimeError("cannot add same NotebookTab object to "
                               "multiple notebooks")
        yield
        self.notebook = notebook
        self.config.update(self._initial_options)

    def hide(self):
        """Calls ``pathName hide`` documented in :man:`ttk_notebook(3tk)`.

        Use :meth:`unhide` to make the tab visible again. :exc:`RuntimeError`
        is raised if the tab has not been added to a notebook.
        """
        self._check_in_notebook()
        self.notebook._call(None, self.notebook, 'hide', self.widget)

    def unhide(self):
        """Undoes a :meth:`hide` call."""
        self._check_in_notebook()
        self.notebook._call(None, self.notebook, 'add', self.widget)


class Notebook(ChildMixin, Widget, collections.abc.MutableSequence):
    """This is the notebook widget.

    For doing advanced magic, you can create a new class that inherits from
    :class:`.Notebook`. Here are some facts that can be useful when deciding
    which methods to override:

    * The only method that creates new :class:`.NotebookTab` objects is
      ``__getitem__()``. When you do ``notebook[index]``, Python actually does
      ``notebook.__getitem__(index)``. Other list-like things are guaranteed to
      call ``__getitem__()`` to get the tab objects.
    * The only method that deletes :class:`.NotebookTab` objects from the
      notebook is ``__delitem__()``. ``del notebook[index]`` does
      ``notebook.__delitem__(index)``, which calls ``pathName forget``
      documented in :man:`ttk_notebook(3tk)`.
    * The only method that adds existing :class:`.NotebookTab` objects to the
      notebook is :meth:`insert`. Other methods call it as well; for example,
      ``notebook.append(tab)`` does ``notebook.insert(len(notebook), tab)``.

    As usual, use :func:`super` when overriding.
    """

    def __init__(self, parent, **kwargs):
        super().__init__('ttk::notebook', parent, **kwargs)

    def __len__(self):
        return self._call(int, self, 'index', 'end')

    @needs_main_thread
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Notebook is not supported")

        # there seems to be no way to get a widget by index without getting a
        # list of all widgets
        widgets = self._call([Widget], self, 'tabs')
        return NotebookTab._from_notebook_and_widget(self, widgets[index])

    @needs_main_thread
    def __setitem__(self, index, tab):
        del self[index]
        self.insert(index, tab)

    @needs_main_thread
    def __delitem__(self, index, tab):
        tab = self[index]
        tab.notebook = None
        self._call(None, self, 'forget', tab.widget)

    @needs_main_thread
    def insert(self, index, tab):
        if not isinstance(tab, NotebookTab):
            raise TypeError("expected a NotebookTab, got %r" % (tab,))

        # lists do this
        if index < 0:
            index += len(self)
        if index < 0:
            index = 0
        if index > len(self):
            index = len(self)

        with tab._adding_to_notebook_helper(self):
            self._call(None, self, 'insert', index, tab.widget)

    @needs_main_thread
    def move(self, tab, new_index):
        """
        Move a tab so that after calling this, ``self[new_index]`` is ``tab``.
        """
        if tab not in self:
            raise ValueError("add the tab to the notebook first, "
                             "then you can move it")
        self._call(None, self, 'insert', index, tab.widget)

    @property
    @needs_main_thread
    def selected_tab(self):
        widget = self._call(Widget, self, 'select')

        # return a tab object instead of a widget
        index = self._call([Widget], self, 'tabs').index(widget)
        return self[index]

    @selected_tab.setter
    def selected_tab(self, tab):
        self._call(None, self, 'select', tab.widget)
