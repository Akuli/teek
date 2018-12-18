import collections.abc
import contextlib
import os
import re

import pytest

import pythotk as tk


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def _get_all_subclasses(claas):
    for subclass in claas.__subclasses__():
        yield subclass
        yield from _get_all_subclasses(subclass)


def test_all_widgets_fixture(all_widgets):
    assert {type(widget) for widget in all_widgets} == {
        claas for claas in _get_all_subclasses(tk.Widget)
        if claas.__module__.startswith('pythotk.')
    }


def test_manual_page_links_in_docstrings(all_widgets):
    for claas in map(type, all_widgets):
        if claas is not tk.Window:
            text = ('Manual page: :man:`%s(3tk)`'
                    % claas._widget_name.replace('::', '_'))
            assert text in claas.__doc__


def test_that_widget_names_dont_contain_horrible_mistakes(all_widgets):
    for widget in all_widgets:
        if isinstance(widget, tk.Window):
            # it is weird, and it is supposed to be weird
            continue

        class_name = type(widget).__name__
        tcl_command = widget._widget_name
        assert class_name.lower() in tcl_command


def test_tk_class_names(all_widgets):
    for widget in all_widgets:
        if not isinstance(widget, tk.Window):
            winfo_result = tk.tcl_call(str, 'winfo', 'class', widget)
            assert winfo_result == type(widget).tk_class_name

    # special cases
    assert tk.Widget.tk_class_name is None
    assert tk.Window.tk_class_name is None

    class LolWidget(tk.Widget):
        pass

    class LolLabel(tk.Label):
        pass

    assert LolWidget.tk_class_name is None
    assert LolLabel.tk_class_name == 'TLabel'


def test_basic_repr_stuff(monkeypatch):
    monkeypatch.syspath_prepend(DATA_DIR)
    import subclasser

    window = tk.Window()
    frame = tk.Frame(window)
    label1 = tk.Label(window, text='a')
    label2 = subclasser.LolLabel(window, text='b')

    assert repr(label1) == "<pythotk.Label widget: text='a'>"
    assert repr(label2) == "<subclasser.LolLabel widget: text='b'>"
    assert repr(frame) == "<pythotk.Frame widget>"


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


def test_creating_instance_of_wrong_class():
    with pytest.raises(TypeError) as error:
        tk.Widget(None)
    assert "cannot create instances of Widget" in str(error.value)


def test_destroy():
    window = tk.Window()
    label = tk.Label(window)
    frame = tk.Frame(window)
    button = tk.Button(frame)
    widgets = [window, label, button]

    command = tk.create_command(print, str)
    label.command_list.append(command)
    assert tk.tcl_call([str], 'info', 'commands', command) == [command]

    assert window.winfo_children() == [label, frame]
    assert frame.winfo_children() == [button]

    for widget in widgets:
        assert widget.winfo_exists()

    window.destroy()
    for widget in widgets:
        assert not widget.winfo_exists()
        assert repr(widget).startswith('<destroyed ')

    assert tk.tcl_call([str], 'info', 'commands', command) == []

    with pytest.raises(RuntimeError) as error:
        label.config['text'] = 'lel'
    assert str(error.value) == 'the widget has been destroyed'


def test_destroy_with_widget_not_created_in_pythotk():
    window = tk.Window()
    label_name = window.to_tcl() + '.asd'
    tk.tcl_call(None, 'label', label_name)
    assert tk.tcl_call(bool, 'winfo', 'exists', label_name)
    window.destroy()    # should also destroy the label
    assert not tk.tcl_call(bool, 'winfo', 'exists', label_name)


def test_destroy_event():
    window = tk.Window()
    asd = []
    window.bind('<Destroy>', asd.append, event=True)
    tk.quit()
    assert len(asd) == 1


def test_options():
    window = tk.Window()

    for widget in [tk.Button(window), tk.Label(window)]:
        assert 'behaves like a dict' in repr(widget.config)
        assert len(widget.config) == len(list(widget.config))

        # abbreviations aren't allowed, it simplifies the implementation
        # and people aren't aware of abbreviating things in tk anyway
        assert 'text' in widget.config
        assert 'tex' not in widget.config
        with pytest.raises(KeyError):
            widget.config['tex']

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


def test_bind(handy_callback):
    widget = tk.Window()
    assert not widget.bindings.keys()

    @handy_callback
    def tcl_call_bound_callback():
        pass

    @handy_callback
    def pythotk_bound_callback():
        pass

    command = tk.create_command(tcl_call_bound_callback)

    tk.tcl_call(None, 'bind', widget, '<<Asd>>', command)
    assert widget.bindings.keys() == {'<<Asd>>'}
    widget.bind('<<Asd>>', pythotk_bound_callback)
    tk.update()
    tk.tcl_call(None, 'event', 'generate', widget, '<<Asd>>')

    tk.delete_command(command)

    assert tcl_call_bound_callback.ran_once()    # tests binding with +
    assert pythotk_bound_callback.ran_once()

    # some binding strings are equivalent
    assert widget.bindings['<Button-3>'] is widget.bindings['<Button-3>']
    assert widget.bindings['<3>'] is widget.bindings['<Button-3>']

    assert repr(widget.bindings) == '<a bindings object, behaves like a dict>'


def test_bind_class(handy_callback):
    @handy_callback
    def class_callback():
        pass

    @handy_callback
    def all_callback():
        pass

    tk.Text.bind_class('<<Lol>>', class_callback)
    tk.Widget.bind_class('<<Lol>>', all_callback)

    text = tk.Text(tk.Window())
    text.pack()
    tk.update()     # make sure that virtual events work
    text.event_generate('<<Lol>>')

    assert class_callback.ran_once()
    assert all_callback.ran_once()

    class FunnyWidget(tk.Widget):
        pass

    with pytest.raises(AttributeError) as error:
        text.class_bindings

    assert str(error.value) == (
        "the class_bindings attribute must be used like Text.class_bindings, "
        "not like some_text_instance.class_bindings")

    with pytest.raises(AttributeError) as error2:
        FunnyWidget.class_bindings

    with pytest.raises(AttributeError) as error3:
        FunnyWidget.bind_class('<<Lol>>', print)

    assert str(error2.value) == str(error3.value) == (
        "FunnyWidget cannot be used with class_bindings and bind_class()")


def test_bind_break():
    events = []
    widget = tk.Window()
    widget.bind('<<Asd>>', (lambda: events.append('one')))
    widget.bind('<<Asd>>', (lambda: [events.append('two'), 'break'][1]))  # lol
    widget.bind('<<Asd>>', (lambda: events.append('three')))

    tk.update()     # needed for virtual events to work
    widget.event_generate('<<Asd>>')


def test_event_objects():
    events = []

    widget = tk.Window()
    widget.bind('<<Asd>>', events.append, event=True)
    tk.update()     # needed for virtual events to work
    widget.event_generate('<<Asd>>', data='asd asd')
    event = events.pop()
    assert not events

    # if some of these checks fail, feel free to make them less strict
    assert event.data(str) == 'asd asd'
    assert event.above is None
    assert event.borderwidth is None
    assert event.button is None
    assert event.char == '??'
    assert event.count is None
    assert event.delta is None
    assert event.focus is None
    assert event.height is None
    assert isinstance(event.i_window, int)
    assert event.keycode is None
    assert event.keysym == '??'
    assert event.keysym_num is None
    assert event.mode == '??'
    assert event.override is None
    assert event.place == '??'
    assert event.property_name == '??'
    assert event.root == 0
    assert event.rootx == -1
    assert event.rooty == -1
    assert event.sendevent is False
    assert isinstance(event.serial, int)
    assert event.state == '0'
    assert event.subwindow == 0
    assert event.time == 0
    assert event.type == 35     # see some docs somewhere i dunno why 35
    assert event.widget is widget
    assert event.width is None
    assert event.x == 0
    assert event.y == 0

    regex = r"<Event: data='asd asd', serial=\d+, type=35>"
    assert re.fullmatch(regex, repr(event)) is not None


def test_bind_deletes_tcl_commands(handy_callback):
    widget = tk.Window()
    widget.bind('<Button-1>', print)
    tcl_codes = tk.tcl_call(str, 'bind', widget, '<Button-1>')
    command_string = re.search(r'pythotk_command_\d+', tcl_codes).group(0)

    assert command_string in tk.tcl_call([str], 'info', 'commands')
    widget.destroy()
    assert command_string not in tk.tcl_call([str], 'info', 'commands')


def test_config_types(check_config_types, all_widgets):
    for widget in all_widgets:
        check_config_types(widget.config, type(widget).__name__)


def test_from_tcl():
    window = tk.Window()
    widget_path = window.to_tcl()
    assert isinstance(widget_path, str)

    assert tk.Window.from_tcl(widget_path) is window
    assert tk.Widget.from_tcl(widget_path) is window

    with pytest.raises(TypeError) as error:
        tk.Label.from_tcl(widget_path)
    assert str(error.value).endswith(" is a Window, not a Label")


@pytest.mark.skipif(tk.TK_VERSION < (8, 6), reason="busy is new in Tk 8.6")
def test_busy(all_widgets):
    for widget in all_widgets:
        assert widget.busy_status() is False
        widget.busy_hold()
        assert widget.busy_status() is True
        widget.busy_forget()
        assert widget.busy_status() is False

        with pytest.raises(ZeroDivisionError):
            with widget.busy():
                assert widget.busy_status() is True
                1 / 0

        assert widget.busy_status() is False


def get_counter_value(widget):
    match = re.search(r'\d+$', widget.to_tcl())
    assert match
    return int(match.group(0))


def test_widget_name_bug():
    # this bug occurs when we have 2 classes with the same name
    class Asd(tk.Label):
        pass

    AsdLabel = Asd

    class Asd(tk.Button):
        pass

    AsdButton = Asd

    # it must not be possible to have two Asds with same to_tcl() widget path,
    window = tk.Window()
    label = AsdLabel(window)
    button = AsdButton(window)

    while get_counter_value(label) < get_counter_value(button):
        label = AsdLabel(window)
        assert label.to_tcl() != button.to_tcl()

    while get_counter_value(button) < get_counter_value(label):
        button = AsdButton(window)
        assert label.to_tcl() != button.to_tcl()


def test_winfo_ismapped():
    window = tk.Window()
    tk.update()
    assert window.winfo_ismapped() is True

    frame = tk.Frame(window)
    assert frame.winfo_ismapped() is False
    tk.update()
    assert frame.winfo_ismapped() is False

    frame.pack()
    tk.update()
    assert frame.winfo_ismapped() is True


def test_winfo_width_height():
    window = tk.Window()
    frame = tk.Frame(window, width=123, height=456)
    frame.pack()
    tk.update()
    assert frame.winfo_width() == 123
    assert frame.winfo_height() == 456


def test_focus():
    widget = tk.Window()

    # no good way to actually test this, so let's just make sure it's calls the
    # correct command
    tk.tcl_eval(None, 'rename focus real_focus')
    try:
        log = []
        tk.tcl_eval(None, '''
        proc focus {args} {
            %s $args
        }
        ''' % tk.create_command(log.append, [str]))
        widget.focus()
        widget.focus(force=True)
        assert log == [
            widget.to_tcl(),
            '-force %s' % widget.to_tcl(),
        ]
    finally:
        tk.tcl_eval(None, '''
        catch {
            rename focus {}
        }
        rename real_focus focus
        ''')


def test_state():
    assert tk.Menu().state is None
    assert tk.Toplevel().state is None

    state = tk.Button(tk.Window()).state
    assert state is not None
    assert isinstance(state, collections.abc.Set)
    assert isinstance(state, collections.abc.MutableSet)

    assert 'disabled' not in state

    state.add('disabled')
    assert 'disabled' in state
    state.add('disabled')
    assert 'disabled' in state

    state.discard('disabled')
    assert 'disabled' not in state
    state.discard('disabled')
    assert 'disabled' not in state

    state.add('disabled')
    state.remove('disabled')
    assert 'disabled' not in state
    with pytest.raises(KeyError):
        state.remove('disabled')

    assert not state
    assert repr(state) == "<state set: []>"
    state.add('disabled')
    assert state
    assert repr(state) == "<state set: ['disabled']>"
