# most of the tests don't destroy the widgets they use, all widgets are
# destroyed the next time quit() is called or python exits anyway
import contextlib
import itertools
import tkinder as tk

import pytest

_flatten = itertools.chain.from_iterable


@contextlib.contextmanager
def _tkinter_hint(bad, assigning):
    with pytest.raises(TypeError) as error:
        yield

    good = "widget.config['option']"
    if assigning:
        good += " = value"
    assert str(error.value) == "use %s, not %s" % (good, bad)


def test_tkinter_hints():
    window = tk.Window()

    with _tkinter_hint("widget['option']", assigning=False):
        window['whatever']

    # this uses assigning=False because the error message is supposed to
    # be just like the one above
    with _tkinter_hint("widget['option']", assigning=False):
        window['whatever'] = 'blah'

    with _tkinter_hint("widget.config(option=value)", assigning=True):
        window.config(whatever='blah')

    with _tkinter_hint("widget.configure(option=value)", assigning=True):
        window.configure(whatever='blah')


def test_destroy():
    window = tk.Window()
    label = tk.Label(window)
    frame = tk.Frame(window)
    button = tk.Button(frame)
    widgets = [window, label, button]

    assert window.winfo_children() == [label, frame]
    assert frame.winfo_children() == [button]

    for widget in widgets:
        assert widget.winfo_exists()

    window.destroy()
    for widget in widgets:
        assert not widget.winfo_exists()
        assert repr(widget).startswith('<destroyed ')

    with pytest.raises(RuntimeError) as error:
        label.config['text'] = 'lel'
    assert str(error.value) == 'the widget has been destroyed'


def test_window():
    windows = [
        (tk.Window("hello hello"), "hello hello"),
        (tk.Window(), None),
    ]

    for window, default_title in windows:
        assert window.winfo_toplevel() is window
        tk.update()     # you can add more of these if the tests don't work

        assert window.state == 'normal'
        if default_title is not None:
            assert window.title == default_title
            assert repr(default_title) in repr(window)

        window.title = "hello hello"
        assert window.title == "hello hello"

        for method, state in [(window.withdraw, 'withdrawn'),
                              (window.iconify, 'iconic')]:
            method()
            assert window.state == state
            assert ("state='%s'" % state) in repr(window)
            window.deiconify()
            assert window.state == 'normal'
            assert "state='normal'" not in repr(window)

            window.state = state        # should do same as method()
            assert window.state == state
            window.deiconify()
            assert window.state == 'normal'

    not_a_window = tk.Frame(windows[0][0])
    assert not hasattr(not_a_window, 'title')


def test_geometry():
    window = tk.Window()

    # namedtuple features
    geometry = window.geometry()
    assert geometry == geometry
    assert hash(geometry) == hash(geometry)
    assert repr(geometry).startswith('Geometry(')

    window.geometry(300, 400)
    tk.update()
    assert window.geometry()[:2] == (300, 400)

    window.geometry(x=123, y=456)
    tk.update()
    assert window.geometry() == (300, 400, 123, 456)

    window.geometry(100, 200, 300, 400)
    tk.update()
    assert window.geometry() == (100, 200, 300, 400)

    for pair in [('width', 'height'), ('x', 'y')]:
        with pytest.raises(TypeError) as error:
            window.geometry(**{pair[0]: 123})
        assert str(error.value) == 'specify both %s and %s, or neither' % pair


_COLOR_OPTIONS = [
    'foreground', 'fg', 'background', 'bg',
    'activeforeground', 'activebackground',
    'disabledforeground', 'disabledbackground',
    'highlightcolor', 'highlightbackground',
    'selectforeground', 'selectbackground',
    'insertbackground',
]
_ALIASES = [('fg', 'foreground'), ('bg', 'background')]
_COLORS = ['red', 'Red', '#ff0000', '#F00', '#fFf000000']


def test_options():
    window = tk.Window()

    for widget in [tk.Button(window), tk.Label(window)]:
        assert repr(widget.widget_path) in repr(widget.config)
        assert 'behaves like a dict' in repr(widget.config)
        assert len(widget.config) == len(list(widget.config))

        with pytest.raises(KeyError):
            # abbreviations aren't allowed, it simplifies the implementation
            # and people aren't aware of abbreviating things in tk anyway
            widget.config['foregro']

        for option in (_COLOR_OPTIONS & widget.config.keys()):
            for color in _COLORS:
                widget.config[option] = color
                assert widget.config[option] == '#ff0000', option

                if option in _flatten(_ALIASES):
                    for a, b in _ALIASES:
                        assert widget.config[a] == widget.config[b]

        with pytest.raises(TypeError):
            widget.config.pop('text')

        # buttons are tested below, this makes sure that windows and
        # labels don't do something weird when they get an option that
        # they shouldn't support
        if not isinstance(widget, tk.Button):
            with pytest.raises(KeyError):
                widget.config['command'] = print

    widget1 = tk.Label(window, 'lol')
    widget1.config.update({'fg': 'blue', 'bg': 'red'})

    widget2 = tk.Label(window, **widget1.config)
    assert widget1.config == widget2.config
    widget2.config['fg'] = 'yellow'
    assert widget1.config != widget2.config


def test_labels():
    window = tk.Window()

    label = tk.Label(window)
    assert "text=''" in repr(label)
    assert label.config['text'] == ''

    label.config.update({'text': 'new text', 'bg': 'blue'})
    assert label.config['text'] == 'new text'
    assert "text='new text'" in repr(label)

    label2 = tk.Label(window, 'new text', bg='blue')
    assert label.config == label2.config


def test_buttons(capsys):
    window = tk.Window()
    stuff = []

    button1 = tk.Button(window, fg='blue')
    button2 = tk.Button(window, 'click me', fg='blue')
    button3 = tk.Button(window, 'click me',
                        (lambda: stuff.append(3)), fg='blue')

    assert "text=''" in repr(button1)
    assert "text='click me'" in repr(button2)
    assert "text='click me'" in repr(button3)

    assert (button1.config['fg'] == button2.config['fg'] ==
            button3.config['fg'] == '#0000ff')
    assert button1.config['text'] == ''
    assert button2.config['text'] == button3.config['text'] == 'click me'

    for button in [button1, button2, button3]:
        assert 'command' not in button.config
        with pytest.raises(ValueError) as error:
            button.config['command'] = print
        assert str(error.value).endswith(
            "use the on_click attribute or an initialization argument instead")

    # ideally there would be some way to click the button virtually and
    # let tk handle it, but i haven't gotten anything like that to work
    button1.on_click.run()
    button2.on_click.run()
    assert stuff == []
    button3.on_click.run()
    assert stuff == [3]

    button1.on_click.connect(stuff.append, args=[1])
    button2.on_click.connect(stuff.append, args=[2])
    button3.on_click.connect(stuff.append, args=['wolo'])
    button3.on_click.connect(stuff.append, args=['wolo'])

    stuff.clear()
    for button in [button1, button2, button3]:
        button.on_click.run()
    assert stuff == [1, 2, 3, 'wolo', 'wolo']

    def oops():
        raise ValueError("shit")

    assert capsys.readouterr() == ('', '')
    button1.on_click.connect(oops)
    button1.on_click.run()
    output, errors = capsys.readouterr()
    assert not output
    assert 'button1.on_click.connect(oops)' in errors


def test_from_widget_path():
    window = tk.Window()
    string = window.widget_path
    assert isinstance(string, str)

    assert tk.Window.from_widget_path(string) is window
    assert tk.Widget.from_widget_path(string) is window

    with pytest.raises(TypeError) as error:
        tk.Label.from_widget_path(string)
    assert str(error.value).endswith(" is a Window, not a Label")
