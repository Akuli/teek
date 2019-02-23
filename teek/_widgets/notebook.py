import collections.abc
import weakref

import teek
from teek._structures import ConfigDict
from teek._tcl_calls import make_thread_safe
from teek._widgets.base import ChildMixin, Widget


class TabConfigDict(ConfigDict):

    def __init__(self, tab):
        self._tab = tab
        super().__init__()
        self._types.update({
            'state': str,
            'sticky': str,
            'padding': [teek.ScreenDistance],
            'text': str,
            'image': teek.Image,
            'compound': str,
            'underline': int,
        })

    # self._tab.widget.parent is the notebook, lol
    def _set(self, option, value):
        self._tab._check_in_notebook()
        teek.tcl_call(None, self._tab.widget.parent,
                      'tab', self._tab.widget, '-' + option, value)

    def _get(self, option):
        self._tab._check_in_notebook()
        return teek.tcl_call(self._types.get(option, str),
                             self._tab.widget.parent, 'tab', self._tab.widget,
                             '-' + option)

    def _list_options(self):
        self._tab._check_in_notebook()
        for option in teek.tcl_call({}, self._tab.widget.parent,
                                    'tab', self._tab.widget):
            yield option.lstrip('-')


class NotebookTab:
    """
    Represents a tab that is in a notebook, or is ready to be added to a
    notebook.

    The *widget* must be a child widget of a :class:`.Notebook` widget. Each
    :class:`.NotebookTab` belongs to the widget's parent notebook; for example,
    if you create a tab like this...
    ::

        tab = teek.NotebookTab(teek.Label(asd_notebook, "hello"))

    ...then the tab cannot be added to any other notebook widget than
    ``asd_notebook``, because ``asd_notebook`` is the parent widget of the
    label.

    Most methods raise :exc:`RuntimeError` if the tab has not been added to the
    notebook yet. This includes doing pretty much anything with :attr:`config`.

    For convenience, options can be passed when creating a
    :class:`.NotebookTab`, so that this...
    ::

        notebook.append(teek.NotebookTab(some_widget, text="Tab Title"))

    ...does the same thing as this::

        tab = teek.NotebookTab(some_widget, text="Tab Title")
        notebook.append(tab)
        tab.config['text'] = "Tab Title"

    There are never multiple :class:`NotebookTab` objects that represent the
    same tab.

    .. attribute:: config

        Similar to the ``config`` attribute that widgets have. The available
        options are documented as ``TAB OPTIONS`` in :man:`ttk_notebook(3tk)`.
        Attempting to use this raises :exc:`RuntimeError` if the tab hasn't
        been added to the notebook yet.

    .. attribute:: widget

        This attribute and initialization argument is the widget in the tab. It
        should be a child widget of the notebook. Use ``tab.widget.parent`` to
        access the :class:`.Notebook` that the tab belongs to.

    .. attribute:: initial_options

        A dict of keyword arguments passed to NotebookTab. When the tab is
        added to the notebook for the first time, :attr:`.config` is updated
        from this dict.
    """

    @make_thread_safe
    def __init__(self, widget, **kwargs):
        if not isinstance(widget.parent, Notebook):
            raise ValueError("widgets of NotebookTabs must be child widgets "
                             "of a Notebook, but %r is a child widget of %r"
                             % (widget, widget.parent))

        if widget in widget.parent._tab_objects:
            raise RuntimeError("there is already a NotebookTab of %r"
                               % (widget,))

        self.widget = widget
        self.config = TabConfigDict(self)
        self.initial_options = kwargs

        # if anything above failed for whatever reason, this tab object is
        # broken, and in that case this doesn't run, which is good
        widget.parent._tab_objects[widget] = self

    def __repr__(self):
        item_reprs = ['%s=%r' % pair for pair in self.initial_options.items()]
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join([repr(self.widget)] + item_reprs))

    def _check_in_notebook(self):
        if self not in self.widget.parent:
            raise RuntimeError("the tab is not in the notebook yet")

    def hide(self):
        """Call ``pathName hide`` documented in :man:`ttk_notebook(3tk)`.

        Use :meth:`unhide` to make the tab visible again. :exc:`RuntimeError`
        is raised if the tab has not been added to a notebook.
        """
        self._check_in_notebook()
        self.widget.parent._call(None, self.widget.parent, 'hide', self.widget)

    def unhide(self):
        """Undo a :meth:`hide` call."""
        self._check_in_notebook()
        self.widget.parent._call(None, self.widget.parent, 'add', self.widget)


class Notebook(ChildMixin, Widget, collections.abc.MutableSequence):
    """This is the notebook widget.

    If you try to add a tab that is already in the notebook, that tab will be
    moved. For example:

    >>> notebook = teek.Notebook(teek.Window())
    >>> tab1 = teek.NotebookTab(teek.Label(notebook, text="1"), text="One")
    >>> tab2 = teek.NotebookTab(teek.Label(notebook, text="2"), text="Two")
    >>> notebook.extend([tab1, tab2])
    >>> list(notebook)      # doctest: +NORMALIZE_WHITESPACE
    [NotebookTab(<teek.Label widget: text='1'>, text='One'),
     NotebookTab(<teek.Label widget: text='2'>, text='Two')]
    >>> notebook.append(notebook[0])
    >>> list(notebook)      # doctest: +NORMALIZE_WHITESPACE
    [NotebookTab(<teek.Label widget: text='2'>, text='Two'),
     NotebookTab(<teek.Label widget: text='1'>, text='One')]

    For doing advanced magic, you can create a new class that inherits from
    :class:`.Notebook`. Here are some facts that can be useful when deciding
    which methods to override:

    * Override ``__delitem__()`` to customize removing tabs from the notebook.
      A deletion like ``del notebook[index]``
      does ``notebook.__delitem__(index)``, which calls ``pathName forget``
      documented in :man:`ttk_notebook(3tk)`. All other kinds of deletions call
      ``__delitem__`` as well.
    * Override ``insert()`` if you want to customize adding new tabs to the
      notebook. The ``insert`` method is called every time when a new tab is
      added with any method. Make sure that your override is compatible with
      the ``insert()`` method of :class:`collections.abc.MutableSequence`, and
      make sure that only the order of the tabs changes if the new tab is
      already in the notebook.
    * Bind to ``<<NotebookTabChanged>>`` if you want to customize what happens
      when a different tab is selected. That runs when the user changes a tab
      or the tab is changed with the :attr:`.selected_tab` property.
      ``<<NotebookTabChanged>>`` is documented in the ``VIRTUAL EVENTS``
      section of :man:`ttk_notebook(3tk)`.

    As usual, use :func:`super` when overriding.

    Manual page: :man:`ttk_notebook(3tk)`
    """

    _widget_name = 'ttk::notebook'
    tk_class_name = 'TNotebook'

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # keys are widgets, and values are NotebookTabs that can be garbage
        # collected when the widgets are garbage collected
        self._tab_objects = weakref.WeakKeyDictionary()

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'width': int,
            'height': int,
        })

    def get_tab_by_widget(self, widget):
        """
        Finds a :class:`.NotebookTab` object by the
        :attr:`~.NotebookTab.widget` attribute.

        If there is no tab with the given widget, a new tab is created.

        >>> notebook = teek.Notebook(teek.Window())
        >>> label = teek.Label(notebook, text='lol')
        >>> tab = teek.NotebookTab(label)
        >>> notebook.append(tab)
        >>> tab
        NotebookTab(<teek.Label widget: text='lol'>)
        >>> notebook.get_tab_by_widget(label)
        NotebookTab(<teek.Label widget: text='lol'>)
        """
        try:
            return self._tab_objects[widget]
        except KeyError:
            if widget.parent is not self:
                raise ValueError(
                    "expected a widget with the notebook as its parent, "
                    "got " + repr(widget))

            # this can happen if the tab was added with a Tcl call
            return NotebookTab(widget)  # adds the new tab to self._tab_objects

    def _repr_parts(self):
        return ["contains %d tabs" % len(self)]

    def __len__(self):
        return self._call(int, self, 'index', 'end')

    @make_thread_safe
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise TypeError("slicing a Notebook is not supported")

        # there seems to be no way to get a widget by index without getting a
        # list of all widgets
        widgets = self._call([Widget], self, 'tabs')
        return self.get_tab_by_widget(widgets[index])

    @make_thread_safe
    def __setitem__(self, index, tab):
        del self[index]
        self.insert(index, tab)

    @make_thread_safe
    def __delitem__(self, index):
        self._call(None, self, 'forget', self[index].widget)

    # yes, an empty docstring does the right thing here, otherwise the
    # docstring seems to be copied from MutableSequence which is not what i
    # want because MutableSequence's docstring:
    #   * doesn't explain the details
    #   * is not good RST
    @make_thread_safe
    def insert(self, index, tab):
        """"""
        if not isinstance(tab, NotebookTab):
            raise TypeError("expected a NotebookTab object, got %r" % (tab,))
        if tab.widget.parent is not self:
            raise ValueError("cannot add %r's tab to %r"
                             % (tab.widget.parent, self))

        # lists do this
        if index < 0:
            index += len(self)
        if index < 0:
            index = 0
        if index > len(self):
            index = len(self)

        # because ttk is fun, isn't it
        if index == len(self):
            index = 'end'

        moving_only = (tab in self)
        self._call(None, self, 'insert', index, tab.widget)
        if not moving_only:
            tab.config.update(tab.initial_options)

    @make_thread_safe
    def move(self, tab, new_index):
        """
        Move a tab so that after calling this, ``self[new_index]`` is ``tab``.

        The new index may be negative. :class:`IndexError` is raised if the
        index is not in the correct range.
        """
        if tab not in self:
            raise ValueError("add the tab to the notebook first, "
                             "then you can move it")

        # support negative indexes, and raise IndexErrors accordingly
        new_index = range(len(self))[new_index]
        self._call(None, self, 'insert', new_index, tab.widget)

    @property
    @make_thread_safe
    def selected_tab(self):
        """This is the tab that the user is currently looking at.

        This is ``None`` if there are no tabs in the notebook. You can set this
        to any other tab in the notebook to change the currently selected tab.
        """
        widget = self._call(Widget, self, 'select')
        if widget is None:
            return None

        # return a tab object instead of a widget
        index = self._call([Widget], self, 'tabs').index(widget)
        return self[index]

    @selected_tab.setter
    def selected_tab(self, tab):
        self._call(None, self, 'select', tab.widget)

    @make_thread_safe
    def append_and_select(self, tab):
        """A convenient way to add a tab to the notebook and select it.

        ``notebook.append_and_select(tab)`` is same as::

            notebook.append(tab)
            notebook.selected_tab = tab
        """
        self.append(tab)
        self.selected_tab = tab
