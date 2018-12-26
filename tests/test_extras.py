import functools
import time
import types
import webbrowser

import pytest

import pythotk as tk
from pythotk._widgets.windows import WmMixin
from pythotk.extras import cross_platform, links, more_dialogs, tooltips


def run_event_loop(for_how_long):
    # this is dumb
    start = time.time()
    while time.time() < start + for_how_long:
        tk.update()


@pytest.mark.slow
def test_set_tooltip():
    window = tk.Window()
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


def test_bind_tab_key():
    what_happened = []

    def callback1(shifted):
        what_happened.append((1, shifted))

    def callback2(shifted, event):
        assert event == 'fake event'
        what_happened.append((2, shifted))

    widget = tk.Window()
    cross_platform.bind_tab_key(widget, callback1)
    cross_platform.bind_tab_key(widget, callback2, event=True)

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


def test_ask_string(handy_callback, monkeypatch):
    def validator(string):
        if string not in ('asd', 'wat'):
            raise ValueError
        return string.upper()

    real_run = more_dialogs._EntryDialog.run

    @handy_callback
    def fake_run(entrydialog):

        @handy_callback
        def fake_wait_window():
            [label] = [widget for widget in entrydialog.window.winfo_children()
                       if isinstance(widget, tk.Label)]
            [entry] = [widget for widget in entrydialog.window.winfo_children()
                       if isinstance(widget, tk.Entry)]

            assert entrydialog.window.toplevel.title == 'A'
            assert label.config['text'] == 'B'

            def get_stuff():
                assert entry.text == entrydialog.var.get()
                return (entry.text, entrydialog.ok_button.config['state'],
                        entrydialog.result)

            assert get_stuff() == ('boo', 'disabled', None)
            entry.text = 'a'
            assert get_stuff() == ('a', 'disabled', None)
            entry.text = 'asd'
            assert get_stuff() == ('asd', 'normal', 'ASD')
            entry.text = 'b'
            assert get_stuff() == ('b', 'disabled', None)
            entry.text = 'wat'
            assert get_stuff() == ('wat', 'normal', 'WAT')
            entry.text = 'c'
            assert get_stuff() == ('c', 'disabled', None)

            # the button is disabled now, so on_ok must do nothing
            entrydialog.on_ok()
            assert get_stuff() == ('c', 'disabled', None)
            assert entrydialog.window.winfo_exists()

            entry.text = 'wat'
            assert get_stuff() == ('wat', 'normal', 'WAT')
            entrydialog.on_ok()
            assert not entrydialog.window.winfo_exists()

        entrydialog.window.wait_window = fake_wait_window
        result = real_run(entrydialog)
        assert fake_wait_window.ran_once()
        return result

    monkeypatch.setattr(more_dialogs._EntryDialog, 'run', fake_run)
    assert more_dialogs.ask_string(
        'A', 'B', validator=validator, initial_value='boo',
        parent=tk.Window()) == 'WAT'
    assert fake_run.ran_once()


def test_ask_string_canceling(handy_callback, monkeypatch):
    @handy_callback
    def fake_run(entrydialog):
        [entry] = [widget for widget in entrydialog.window.winfo_children()
                   if isinstance(widget, tk.Entry)]
        entry.text = 'a'

        assert entrydialog.window.winfo_exists()
        assert entrydialog.result == 'a'
        entrydialog.on_cancel()
        assert not entrydialog.window.winfo_exists()
        assert entrydialog.result is None

    monkeypatch.setattr(more_dialogs._EntryDialog, 'run', fake_run)
    more_dialogs.ask_string('A', 'B')
    assert fake_run.ran_once()


def test_ask_integer(handy_callback, monkeypatch):
    with pytest.raises(ValueError):
        more_dialogs.ask_integer('a', 'b', range(10, 1, -1))

    real_entrydialog = more_dialogs._EntryDialog

    @handy_callback
    def fake_entrydialog(*args):
        a, b, creator, validator, initial_value, parent = args
        assert a == 'a'
        assert b == 'b'
        assert callable(creator)
        assert callable(validator)
        assert initial_value == initial
        assert parent is None or isinstance(parent, WmMixin)

        entrydialog = real_entrydialog(*args)
        entrydialog.run = lambda: 123

        [spinbox] = [widget for widget in entrydialog.window.winfo_children()
                     if isinstance(widget, tk.Spinbox)]

        assert spinbox.text == str(initial)
        assert entrydialog.result == initial
        spinbox.text = 'asd'
        assert entrydialog.result is None
        spinbox.text = '12345678'
        assert entrydialog.result is None
        spinbox.text = str(initial)
        assert entrydialog.result == initial

        for item in spinbox_config.items():
            assert item in list(spinbox.config.items())

        return entrydialog

    monkeypatch.setattr(more_dialogs, '_EntryDialog', fake_entrydialog)
    assert fake_entrydialog.ran == 0

    spinbox_config = {'from': 10, 'to': 30, 'increment': 5}
    initial = 10
    assert more_dialogs.ask_integer('a', 'b', range(10, 33, 5)) == 123
    assert fake_entrydialog.ran == 1

    # the spinbox's config contains strings because spinboxes can be used for
    # non-integer things too
    spinbox_config = {'values': ['1', '4', '3']}
    initial = 1
    assert more_dialogs.ask_integer('a', 'b', [1, 4, 3]) == 123
    assert fake_entrydialog.ran == 2

    initial = 4
    assert more_dialogs.ask_integer('a', 'b', [1, 4, 3],
                                    initial_value=4, parent=tk.Window()) == 123
    assert fake_entrydialog.ran == 3

    with pytest.raises(ValueError):
        more_dialogs.ask_integer('a', 'b', [1, 4, 3], initial_value=666)


def test_links_clicking():
    text = tk.Text(tk.Window())

    stuff = []
    links.add_function_link(
        text, 'abc', functools.partial(stuff.append, 1))
    links.add_function_link(
        text, '123', functools.partial(stuff.append, 2), (1, 2))
    assert text.get() == 'ab123c'

    all_tag_names = (tag.name for tag in text.get_all_tags())
    assert {'pythotk-extras-link-1',
            'pythotk-extras-link-2',
            'pythotk-extras-link-common'}.issubset(all_tag_names)

    text.get_tag('pythotk-extras-link-1').bindings['<1>'].run(None)
    text.get_tag('pythotk-extras-link-2').bindings['<1>'].run(None)
    assert stuff == [1, 2]


def test_links_cursor_changes():
    text = tk.Text(tk.Window())
    text.config['cursor'] = 'clock'

    links.add_function_link(text, 'abc', print)
    assert text.config['cursor'] == 'clock'

    for binding, cursor in [('<Leave>', 'clock'),
                            ('<Enter>', 'hand2'),
                            ('<Leave>', 'clock')]:
        text.get_tag('pythotk-extras-link-common').bindings[binding].run(None)
        assert text.config['cursor'] == cursor


URL = 'https://github.com/Akuli/pythotk'


def test_add_url_link(monkeypatch, handy_callback):
    stuff = []
    monkeypatch.setattr(webbrowser, 'open', stuff.append)

    text = tk.Text(tk.Window())
    links.add_url_link(text, 'asd', URL)
    text.get_tag('pythotk-extras-link-1').bindings['<1>'].run(None)
    assert stuff == [URL]
