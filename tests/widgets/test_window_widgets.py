import platform
import os
import time

import pytest

import teek


SMILEY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'smiley.gif')


def test_window():
    windows = [
        (teek.Window("hello hello"), "hello hello"),
        (teek.Window(), None),
    ]

    for window, default_title in windows:
        assert window.winfo_toplevel() is window.toplevel
        assert isinstance(window.toplevel, teek.Toplevel)
        teek.update()     # you can add more of these if the tests don't work

        assert window.wm_state == 'normal'
        if default_title is not None:
            assert window.title == default_title
            assert repr(default_title) in repr(window)

        window.title = "hello hello"
        assert window.title == "hello hello"

    not_a_window = teek.Frame(teek.Window())
    assert not hasattr(not_a_window, 'title')


@pytest.mark.skipif('CI' in os.environ,
                    reason=("relies on non-guaranteed details about how "
                            "window managers work or something like that"))
def test_window_states():
    window = teek.Window()
    for method, state in [(window.withdraw, 'withdrawn'),
                          (window.iconify, 'iconic')]:
        method()
        teek.update()
        assert window.wm_state == state
        assert ("wm_state='%s'" % state) in repr(window)
        window.deiconify()
        teek.update()
        assert window.wm_state == 'normal'
        assert "wm_state='normal'" not in repr(window)

        window.wm_state = state        # should do same as method()
        teek.update()
        assert window.wm_state == state
        window.deiconify()
        teek.update()
        assert window.wm_state == 'normal'


def test_window_closing():
    for window in [teek.Window(), teek.Toplevel()]:
        # on_delete_window should NOT be connected to anything by default
        with pytest.raises(ValueError):
            window.on_delete_window.disconnect(teek.quit)
        with pytest.raises(ValueError):
            window.on_delete_window.disconnect(window.destroy)

        # there are more callback tests elsewhere, but just to be sure
        window.on_delete_window.connect(window.destroy)
        window.on_delete_window.disconnect(window.destroy)
        with pytest.raises(ValueError):
            window.on_delete_window.disconnect(window.destroy)

        assert window.winfo_exists()
        window.destroy()
        assert not window.winfo_exists()


def test_geometry():
    window = teek.Window()

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
    window = teek.Window()
    with pytest.raises(TypeError) as error:
        window.geometry('200x300')
    assert "use widget.geometry(width, height)" in str(error.value)


@pytest.mark.skipif(platform.system() == "Windows",
                    reason=("actual windows window manager behavior"
                            "is different than the test expects"))
def test_geometry_changes():
    window = teek.Window()

    window.geometry(300, 400)
    teek.update()
    assert window.geometry()[:2] == (300, 400)

    window.geometry(x=123, y=456)
    teek.update()
    assert window.geometry() == (300, 400, 123, 456)

    window.geometry(100, 200, 300, 400)
    teek.update()
    assert window.geometry() == (100, 200, 300, 400)


def test_minsize_maxsize():
    window = teek.Window()
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


def test_iconphoto(fake_command):
    image1 = teek.Image(file=SMILEY_PATH)
    image2 = image1.copy()

    widget = teek.Toplevel()

    with fake_command('wm') as called:
        widget.iconphoto(image1)
        widget.iconphoto(image1, image2)
        assert called == [
            ['iconphoto', widget.to_tcl(), image1.to_tcl()],
            ['iconphoto', widget.to_tcl(), image1.to_tcl(), image2.to_tcl()],
        ]


def test_transient():
    window1 = teek.Window()
    window2 = teek.Window()
    toplevel = teek.Toplevel()

    window1.transient = window2
    assert window1.transient is window2.toplevel
    window1.transient = toplevel
    assert window1.transient is toplevel


@pytest.mark.slow
def test_wait_window():
    window = teek.Window()

    start = time.time()
    teek.after(500, window.destroy)
    window.wait_window()
    end = time.time()

    assert end - start > 0.5


# 'menu' is an option that Toplevel has and Frame doesn't have, so Window must
# use its toplevel's menu option
def test_window_menu_like_options_fallback_to_toplevel_options():
    window = teek.Window()
    toplevel = window.toplevel
    frame = teek.Frame(window)
    menu = teek.Menu()

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
    assert isinstance(window.config['width'], teek.ScreenDistance)
