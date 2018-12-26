import platform
import os
import time

import pytest

import pythotk as tk


SMILEY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'smiley.gif')


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


def test_geometry_tkinter_error():
    window = tk.Window()
    with pytest.raises(TypeError) as error:
        window.geometry('200x300')
    assert "use widget.geometry(width, height)" in str(error.value)


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


def test_minsize_maxsize():
    window = tk.Window()
    assert isinstance(window.minsize, tuple)
    assert isinstance(window.maxsize, tuple)
    assert len(window.minsize) == 2
    assert len(window.maxsize) == 2
    assert window.minsize[0] == 1
    assert window.minsize[1] == 1
    assert window.maxsize[0] > 100
    assert window.maxsize[1] > 100

    window.minsize = (12, 34)
    window.maxsize = (56, 78)
    assert window.minsize == (12, 34)
    assert window.maxsize == (56, 78)


def test_iconphoto():
    image1 = tk.Image(file=SMILEY_PATH)
    image2 = image1.copy()

    widget = tk.Toplevel()
    called = []
    fake_widget_command = tk.create_command(
        (lambda *args: called.append(['wm'] + list(args))), [],
        extra_args_type=str)

    tk.tcl_call(None, 'rename', 'wm', 'actual_wm')
    tk.tcl_call(None, 'rename', fake_widget_command, 'wm')
    try:
        widget.iconphoto(image1)
        widget.iconphoto(image1, image2)
    finally:
        tk.delete_command('wm')
        tk.tcl_call(None, 'rename', 'actual_wm', 'wm')

    assert called == [
        ['wm', 'iconphoto', widget.to_tcl(), image1.to_tcl()],
        ['wm', 'iconphoto', widget.to_tcl(), image1.to_tcl(), image2.to_tcl()],
    ]


def test_transient():
    window1 = tk.Window()
    window2 = tk.Window()
    toplevel = tk.Toplevel()

    window1.transient = window2
    assert window1.transient is window2.toplevel
    window1.transient = toplevel
    assert window1.transient is toplevel


@pytest.mark.slow
def test_wait_window():
    window = tk.Window()

    start = time.time()
    tk.after(500, window.destroy)
    window.wait_window()
    end = time.time()

    assert end - start > 0.5


# 'menu' is an option that Toplevel has and Frame doesn't have, so Window must
# use its toplevel's menu option
def test_window_menu_like_options_fallback_to_toplevel_options():
    window = tk.Window()
    toplevel = window.toplevel
    frame = tk.Frame(window)
    menu = tk.Menu()

    assert 'menu' not in frame.config
    assert 'menu' in toplevel.config
    assert 'menu' in window.config

    with pytest.raises(KeyError):
        frame.config['menu']
    assert toplevel.config['menu'] is None
    assert window.config['menu'] is None

    window.config['menu'] = menu
    assert window.config['menu'] is menu
    assert toplevel.config['menu'] is menu
    with pytest.raises(KeyError):
        frame.config['menu']

    window.config['width'] = 100
    assert isinstance(window.config['width'], tk.ScreenDistance)
