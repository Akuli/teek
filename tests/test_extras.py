import time
import types

import pytest
import pythotk as tk


def run_event_loop(for_how_long):
    # this is dumb
    start = time.time()
    while time.time() < start + for_how_long:
        tk.update()


@pytest.mark.slow
def test_set_tooltip():
    window = tk.Window()
    assert not hasattr(window, '_tooltip_manager')

    tk.extras.set_tooltip(window, None)
    assert not hasattr(window, '_tooltip_manager')

    tk.extras.set_tooltip(window, 'Boo')
    assert window._tooltip_manager.text == 'Boo'

    tk.extras.set_tooltip(window, None)
    assert window._tooltip_manager.text is None

    tk.extras.set_tooltip(window, 'lol')
    assert window._tooltip_manager.text == 'lol'

    N = types.SimpleNamespace   # because pep8 line length

    assert not window._tooltip_manager.got_mouse
    window._tooltip_manager.enter(N(widget=window, rootx=123, rooty=456))
    assert window._tooltip_manager.got_mouse
    assert window._tooltip_manager.mousex == 123
    assert window._tooltip_manager.mousey == 456

    window._tooltip_manager.motion(N(rootx=789, rooty=101112))
    assert window._tooltip_manager.got_mouse
    assert window._tooltip_manager.mousex == 789
    assert window._tooltip_manager.mousey == 101112

    run_event_loop(1.1)
    assert window._tooltip_manager.tipwindow is not None
    assert window._tooltip_manager.got_mouse
    window._tooltip_manager.leave(N(widget=window))
    assert not window._tooltip_manager.got_mouse
    assert window._tooltip_manager.tipwindow is None

    # what happens if the window gets destroyed before it's supposed to show?
    window._tooltip_manager.enter(N(widget=window, rootx=1, rooty=2))
    window._tooltip_manager.leave(N(widget=window))
    assert window._tooltip_manager.tipwindow is None
    run_event_loop(1.1)
    assert window._tooltip_manager.tipwindow is None


def test_bind_tab_key():
    what_happened = []

    def callback1(shifted):
        what_happened.append((1, shifted))

    def callback2(shifted, event):
        assert event == 'fake event'
        what_happened.append((2, shifted))

    widget = tk.Window()
    tk.extras.bind_tab_key(widget, callback1)
    tk.extras.bind_tab_key(widget, callback2, event=True)

    # might be nice to trigger a warning when attempting to use <Shift-Tab>
    # on x11
    widget.bindings['<Tab>'].run('fake event')
    if tk.windowingsystem() == 'x11':
        widget.bindings['<ISO_Left_Tab>'].run('fake event')
    else:
        widget.bindings['<Shift-Tab>'].run('fake event')

    assert what_happened == [
        (1, False), (2, False),
        (1, True), (2, True),
    ]
