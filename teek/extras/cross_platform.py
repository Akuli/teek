import functools

import teek


# this is not called bind_tab to avoid confusing with:
#   * \t characters
#   * web browser tabs as in teek.Notebook
def bind_tab_key(widget, callback, **bind_kwargs):
    """A cross-platform way to bind Tab and Shift+Tab.

    Use this function like this::

        from teek.extras import cross_platform

        def on_tab(shifted):
            if shifted:
                print("Shift+Tab was pressed")
            else:
                print("Tab was pressed")

        cross_platform.bind_tab_key(some_widget, on_tab)

    Binding ``'<Tab>'`` works on all systems I've tried it on, but if you also
    want to bind tab presses where the shift key is held down, use this
    function instead.

    This function can also take any of the keyword arguments that
    :meth:`teek.Widget.bind` takes. If you pass ``event=True``, the callback
    will be called like ``callback(shifted, event)``; that is, the ``shifted``
    bool is the first argument, and the event object is the second.
    """
    if teek.windowingsystem() == 'x11':
        # even though the event keysym says Left, holding down the right
        # shift and pressing tab also works :D
        shift_tab = '<ISO_Left_Tab>'
    else:
        shift_tab = '<Shift-Tab>'   # pragma: no cover

    widget.bind('<Tab>', functools.partial(callback, False), **bind_kwargs)
    widget.bind(shift_tab, functools.partial(callback, True), **bind_kwargs)
