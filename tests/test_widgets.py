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
        assert window.winfo_toplevel() is window.toplevel
        assert isinstance(window.toplevel, tk.Toplevel)
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

    not_a_window = tk.Frame(tk.Window())
    assert not hasattr(not_a_window, 'title')


def test_window_closing():
    window = tk.Window()
    window.on_delete_window.run()
    assert not window.winfo_exists()
    assert not window.toplevel.winfo_exists()


def test_geometry():
    window = tk.Window()

    # namedtuple features
    geometry = window.geometry()
    geometry2 = window.geometry()
    assert geometry == geometry2
    assert hash(geometry) == hash(geometry2)
    assert repr(geometry) == repr(geometry2)
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

# this is commented out because ttk widgets don't have color options
#
#_COLOR_OPTIONS = [
#    'foreground', 'fg', 'background', 'bg',
#    'activeforeground', 'activebackground',
#    'disabledforeground', 'disabledbackground',
#    'highlightcolor', 'highlightbackground',
#    'selectforeground', 'selectbackground',
#    'insertbackground',
#]
#_ALIASES = [('fg', 'foreground'), ('bg', 'background')]
#_COLORS = ['red', 'Red', '#ff0000', '#F00', '#fFf000000']


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

#        for option in (_COLOR_OPTIONS & widget.config.keys()):
#            for color in _COLORS:
#                widget.config[option] = color
#                assert widget.config[option] == '#ff0000', option
#
#                if option in _flatten(_ALIASES):
#                    for a, b in _ALIASES:
#                        assert widget.config[a] == widget.config[b]

        with pytest.raises(TypeError):
            widget.config.pop('text')

        # buttons are tested below, this makes sure that windows and
        # labels don't do something weird when they get an option that
        # they shouldn't support
        if not isinstance(widget, tk.Button):
            with pytest.raises(KeyError):
                widget.config['command'] = print

    widget1 = tk.Label(window, 'lol')
    widget1.config.update({'text': 'asd'})
    widget2 = tk.Label(window, text='asd')
    assert widget1.config == widget2.config
    widget2.config['text'] = 'tootie'
    assert widget1.config != widget2.config


def test_labels():
    window = tk.Window()

    label = tk.Label(window)
    assert "text=''" in repr(label)
    assert label.config['text'] == ''

    label.config.update({'text': 'new text'})
    assert label.config['text'] == 'new text'
    assert "text='new text'" in repr(label)

    label2 = tk.Label(window, 'new text')
    assert label.config == label2.config


def test_buttons(capsys):
    window = tk.Window()
    stuff = []

    button1 = tk.Button(window)
    button2 = tk.Button(window, 'click me')
    button3 = tk.Button(window, 'click me', (lambda: stuff.append(3)))

    assert "text=''" in repr(button1)
    assert "text='click me'" in repr(button2)
    assert "text='click me'" in repr(button3)

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


def test_button_invoke():
    button = tk.Button(tk.Window())
    stuff = []
    button.on_click.connect(stuff.append, args=[1])
    button.on_click.connect(stuff.append, args=[2])
    button.invoke()
    assert stuff == [1, 2]


def test_text_widget():
    text = tk.Text(tk.Window())

    # start and end should be namedtuples
    assert isinstance(text.start, tuple)
    assert type(text.start) is not tuple

    # there is nothing in the text widget yet
    assert text.start == text.end == (1, 0)

    text.insert(text.end, 'this is some text\nbla bla bla')
    assert text.get(text.start, text.end) == 'this is some text\nbla bla bla'
    assert text.start == (1, 0)
    assert text.end == (2, 11)
    assert 'contains 2 lines of text' in repr(text)

    text.replace((1, 0), (1, 4), 'lol')
    assert text.get(text.start, text.end) == 'lol is some text\nbla bla bla'

    assert text.get((1, 0), (1, 6)) == 'lol is'
    assert text.get((1, 12), (2, 3)) == 'text\nbla'

    assert text.get() == text.get(text.start, text.end)
    assert text.get(text.start) == text.get(text.start, text.end)

    assert text.start.forward(chars=2, lines=1) == (2, 2)
    assert (text.start.forward(chars=2, lines=1).back(chars=2, lines=1) ==
            text.start)
    assert text.start.forward(chars=100) == text.end

    assert text.start.wordend() == (1, 3)               # after 'lol'
    assert text.start.wordend().linestart() == text.start
    assert (text.start.wordend().lineend() ==
            text.start.forward(lines=1).back(chars=1))

    # Tk's wordstart() seems to be funny, so this is the best test i came
    # up with
    assert text.start.wordstart() == text.start

    # indexes compare nicelys
    assert (text.start <
            text.start.forward(chars=1) <
            text.start.forward(lines=1) <
            text.start.forward(chars=1, lines=1))


def test_text_widget_tags():
    text = tk.Text(tk.Window())
    text.insert(text.start, "asd toot boo")

    assert {tag.name for tag in text.get_all_tags()} == {'sel'}
    assert text.get_tag('asd').name == 'asd'
    assert {tag.name for tag in text.get_all_tags()} == {'sel', 'asd'}

    for tag in [text.get_tag('asd'), text.get_tag('sel')]:
        assert tag is text.get_tag(tag.name)  # returns same tag obj every time

        tag.add((1, 4), (1, 8))
        assert tag.ranges() == [((1, 4), (1, 8))]
        assert all(isinstance(index, type(text.start))
                   for index in _flatten(tag.ranges()))

        assert tag.nextrange((1, 0)) == ((1, 4), (1, 8))
        assert tag.nextrange((1, 0), (1, 4)) is None
        for index in tag.nextrange((1, 0)):
            assert isinstance(index, type(text.start))

        tag.remove()
        assert tag.ranges() == []

    toot = text.get_tag('toot')
    toot.add((1, 4), text.end)
    assert toot.ranges() != []
    toot.delete()
    assert toot not in text.get_all_tags()
    assert toot.ranges() == []
    assert toot not in text.get_all_tags()
    toot['foreground'] = 'blue'
    assert toot in text.get_all_tags()

    # misc other tag properties
    assert toot == toot
    assert toot != tk.Text(tk.Window()).get_tag('toot')   # different widget
    assert toot != 123
    assert hash(toot) == hash(toot)
    assert repr(toot) == "<Text widget tag 'toot': foreground='blue'>"
    with pytest.raises(TypeError):
        del toot['foreground']

    old_names = {tag.name for tag in text.get_all_tags()}
    new_name = text.create_new_tag().name
    assert new_name not in old_names
    assert {tag.name for tag in text.get_all_tags()} == old_names | {new_name}

    tag_names = {'sel', 'asd', 'toot'}
    for tag_name in tag_names:
        text.get_tag(tag_name).add((1, 4), (1, 8))
    assert {tag.name for tag in text.get_all_tags((1, 6))} == tag_names


def test_from_widget_path():
    window = tk.Window()
    string = window.widget_path
    assert isinstance(string, str)

    assert tk.Window.from_widget_path(string) is window
    assert tk.Widget.from_widget_path(string) is window

    with pytest.raises(TypeError) as error:
        tk.Label.from_widget_path(string)
    assert str(error.value).endswith(" is a Window, not a Label")
