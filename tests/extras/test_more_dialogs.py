import pytest

import teek
from teek._widgets.windows import WmMixin
from teek.extras import more_dialogs


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
                       if isinstance(widget, teek.Label)]
            [entry] = [widget for widget in entrydialog.window.winfo_children()
                       if isinstance(widget, teek.Entry)]

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
        parent=teek.Window()) == 'WAT'
    assert fake_run.ran_once()


def test_ask_string_canceling(handy_callback, monkeypatch):
    @handy_callback
    def fake_run(entrydialog):
        [entry] = [widget for widget in entrydialog.window.winfo_children()
                   if isinstance(widget, teek.Entry)]
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
                     if isinstance(widget, teek.Spinbox)]

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
    assert more_dialogs.ask_integer('a', 'b', [1, 4, 3], initial_value=4,
                                    parent=teek.Window()) == 123
    assert fake_entrydialog.ran == 3

    with pytest.raises(ValueError):
        more_dialogs.ask_integer('a', 'b', [1, 4, 3], initial_value=666)
