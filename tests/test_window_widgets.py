import platform
import os

import pytest

import pythotk as tk


def test_window():
    windows = [
        (tk.Window("hello hello"), "hello hello"),
        (tk.Window(), None),
    ]

    for window, default_title in windows:
        assert window.winfo_toplevel() is window.toplevel
        assert isinstance(window.toplevel, tk.Toplevel)
        tk.update()     # you can add more of these if the tests don't work

        assert window.wm_state == 'normal'
        if default_title is not None:
            assert window.title == default_title
            assert repr(default_title) in repr(window)

        window.title = "hello hello"
        assert window.title == "hello hello"

    not_a_window = tk.Frame(tk.Window())
    assert not hasattr(not_a_window, 'title')


@pytest.mark.skipif('CI' in os.environ,
                    reason=("relies on non-guaranteed details about how "
                            "window managers work or something like that"))
def test_window_states():
    window = tk.Window()
    for method, state in [(window.withdraw, 'withdrawn'),
                          (window.iconify, 'iconic')]:
        method()
        tk.update()
        assert window.wm_state == state
        assert ("wm_state='%s'" % state) in repr(window)
        window.deiconify()
        tk.update()
        assert window.wm_state == 'normal'
        assert "wm_state='normal'" not in repr(window)

        window.wm_state = state        # should do same as method()
        tk.update()
        assert window.wm_state == state
        window.deiconify()
        tk.update()
        assert window.wm_state == 'normal'


def test_window_closing():
    for window in [tk.Window(), tk.Toplevel()]:
        # raises an error if not connected, so this also tests the
        # implicit connecting
        window.on_delete_window.disconnect(tk.quit)

        assert window.winfo_exists()
        window.destroy()
        assert not window.winfo_exists()


def test_geometry():
    window = tk.Window()

    # namedtuple features
    geometry = window.geometry()
    geometry2 = window.geometry()
    assert geometry == geometry2
    assert hash(geometry) == hash(geometry2)
    assert repr(geometry) == repr(geometry2)
    assert repr(geometry).startswith('Geometry(')

    for pair in [('width', 'height'), ('x', 'y')]:
        with pytest.raises(TypeError) as error:
            window.geometry(**{pair[0]: 123})
        assert str(error.value) == 'specify both %s and %s, or neither' % pair


@pytest.mark.skipif(platform.system() == "Windows",
                    reason=("actual windows window manager behavior"
                            "is different than the test expects"))
def test_geometry_changes():
    window = tk.Window()

    window.geometry(300, 400)
    tk.update()
    assert window.geometry()[:2] == (300, 400)

    window.geometry(x=123, y=456)
    tk.update()
    assert window.geometry() == (300, 400, 123, 456)

    window.geometry(100, 200, 300, 400)
    tk.update()
    assert window.geometry() == (100, 200, 300, 400)
