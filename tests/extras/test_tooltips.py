import time
import types
import pytest

import teek
from teek.extras import tooltips


def run_event_loop(for_how_long):
    # this is dumb
    start = time.time()
    while time.time() < start + for_how_long:
        teek.update()


@pytest.mark.slow
def test_set_tooltip():
    window = teek.Window()
    assert not hasattr(window, '_tooltip_manager')

    tooltips.set_tooltip(window, None)
    assert not hasattr(window, '_tooltip_manager')

    tooltips.set_tooltip(window, 'Boo')
    assert window._tooltip_manager.text == 'Boo'

    tooltips.set_tooltip(window, None)
    assert window._tooltip_manager.text is None

    tooltips.set_tooltip(window, 'lol')
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
