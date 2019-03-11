import collections.abc
import contextlib
import os
import re

import pytest

import teek


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def _get_all_subclasses(claas):
    for subclass in claas.__subclasses__():
        yield subclass
        yield from _get_all_subclasses(subclass)


def test_all_widgets_fixture(all_widgets):
    assert {type(widget) for widget in all_widgets} == {
        claas for claas in _get_all_subclasses(teek.Widget)
        if claas.__module__.startswith('teek.')
    }


def test_manual_page_links_in_docstrings(all_widgets):
    for claas in map(type, all_widgets):
        if claas is not teek.Window:
            text = ('Manual page: :man:`%s(3tk)`'
                    % claas._widget_name.replace('::', '_'))
            assert text in claas.__doc__


def test_that_widget_names_dont_contain_horrible_mistakes(all_widgets):
    for widget in all_widgets:
        if isinstance(widget, teek.Window):
            # it is weird, and it is supposed to be weird
            continue

        class_name = type(widget).__name__
        tcl_command = widget._widget_name
        assert class_name.lower() in tcl_command


def test_tk_class_names(all_widgets):
    for widget in all_widgets:
        if not isinstance(widget, teek.Window):
            winfo_result = teek.tcl_call(str, 'winfo', 'class', widget)
            assert winfo_result == type(widget).tk_class_name

    # special cases
    assert teek.Widget.tk_class_name is None
    assert teek.Window.tk_class_name is None

    class LolWidget(teek.Widget):
        pass

    class LolLabel(teek.Label):
        pass

    assert LolWidget.tk_class_name is None
    assert LolLabel.tk_class_name == 'TLabel'


def test_basic_repr_stuff(monkeypatch):
    monkeypatch.syspath_prepend(DATA_DIR)
    import subclasser

    window = teek.Window()
    frame = teek.Frame(window)
    label1 = teek.Label(window, text='a')
    label2 = subclasser.LolLabel(window, text='b')

    assert repr(label1) == "<teek.Label widget: text='a'>"
    assert repr(label2) == "<subclasser.LolLabel widget: text='b'>"
    assert repr(frame) == "<teek.Frame widget>"


@contextlib.contextmanager
def _tkinter_hint(bad, assigning):
    with pytest.raises(TypeError) as error:
        yield

    good = "widget.config['option']"
    if assigning:
        good += " = value"
    assert str(error.value) == "use %s, not %s" % (good, bad)


def test_tkinter_hints():
    window = teek.Window()

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
        teek.Widget(None)
    assert "cannot create instances of Widget" in str(error.value)


def test_destroy():
    window = teek.Window()
    label = teek.Label(window)
    frame = teek.Frame(window)
    button = teek.Button(frame)
    widgets = [window, label, button]

    command = teek.create_command(print, str)
    label.command_list.append(command)
    assert teek.tcl_call([str], 'info', 'commands', command) == [command]

    assert window.winfo_children() == [label, frame]
    assert frame.winfo_children() == [button]

    for widget in widgets:
        assert widget.winfo_exists()

    window.destroy()
    for widget in widgets:
        assert not widget.winfo_exists()
        assert repr(widget).startswith('<destroyed ')

    assert teek.tcl_call([str], 'info', 'commands', command) == []

    with pytest.raises(RuntimeError) as error:
        label.config['text'] = 'lel'
    assert str(error.value) == 'the widget has been destroyed'


def test_destroy_with_widget_not_created_in_teek():
    window = teek.Window()
    label_name = window.to_tcl() + '.asd'
    teek.tcl_call(None, 'label', label_name)
    assert teek.tcl_call(bool, 'winfo', 'exists', label_name)
    window.destroy()    # should also destroy the label
    assert not teek.tcl_call(bool, 'winfo', 'exists', label_name)


def test_destroy_event():
    window = teek.Window()
    asd = []
    window.bind('<Destroy>', asd.append, event=True)
    teek.quit()
    assert len(asd) == 1


# the bug was: Widget.destroy() destroyed the widget after deleting
# command_list commands, but <Destroy> binding had a command_list command
def test_destroy_event_bug(handy_callback):
    for gonna_update_in_between in [True, False]:
        frame = teek.Frame(teek.Window())

        @handy_callback
        def on_destroy():
            pass

        frame.bind('<Destroy>', on_destroy)
        if gonna_update_in_between:
            teek.update()

        frame.destroy()
        assert on_destroy.ran_once()
        teek.update()


def test_options():
    window = teek.Window()

    for widget in [teek.Button(window), teek.Label(window)]:
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
        if not isinstance(widget, teek.Button):
            with pytest.raises(KeyError):
                widget.config['command'] = print

    widget1 = teek.Label(window, 'lol')
    widget1.config.update({'text': 'asd'})
    widget2 = teek.Label(window, text='asd')
    assert widget1.config == widget2.config
    widget2.config['text'] = 'tootie'
    assert widget1.config != widget2.config


def test_bind(handy_callback):
    widget = teek.Window()
    assert not widget.bindings.keys()

    @handy_callback
    def tcl_call_bound_callback():
        pass

    @handy_callback
    def teek_bound_callback():
        pass

    command = teek.create_command(tcl_call_bound_callback)

    teek.tcl_call(None, 'bind', widget, '<<Asd>>', command)
    assert widget.bindings.keys() == {'<<Asd>>'}
    widget.bind('<<Asd>>', teek_bound_callback)
    teek.update()
    teek.tcl_call(None, 'event', 'generate', widget, '<<Asd>>')

    teek.delete_command(command)

    assert tcl_call_bound_callback.ran_once()    # tests binding with +
    assert teek_bound_callback.ran_once()

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

    teek.Text.bind_class('<<Lol>>', class_callback)
    teek.Widget.bind_class('<<Lol>>', all_callback)

    text = teek.Text(teek.Window())
    text.pack()
    teek.update()     # make sure that virtual events work
    text.event_generate('<<Lol>>')

    assert class_callback.ran_once()
    assert all_callback.ran_once()

    class FunnyWidget(teek.Widget):
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
    widget = teek.Window()
    widget.bind('<<Asd>>', (lambda: events.append('one')))
    widget.bind('<<Asd>>', (lambda: [events.append('two'), 'break'][1]))  # lol
    widget.bind('<<Asd>>', (lambda: events.append('three')))

    teek.update()     # needed for virtual events to work
    widget.event_generate('<<Asd>>')


def test_event_objects():
    events = []

    widget = teek.Window()
    widget.bind('<<Asd>>', events.append, event=True)
    teek.update()     # needed for virtual events to work
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
    widget = teek.Window()
    widget.bind('<Button-1>', print)
    tcl_codes = teek.tcl_call(str, 'bind', widget, '<Button-1>')
    command_string = re.search(r'teek_command_\d+', tcl_codes).group(0)

    assert command_string in teek.tcl_call([str], 'info', 'commands')
    widget.destroy()
    assert command_string not in teek.tcl_call([str], 'info', 'commands')


def test_config_types(check_config_types, all_widgets):
    for widget in all_widgets:
        check_config_types(widget.config, type(widget).__name__)


def test_from_tcl():
    window = teek.Window()
    widget_path = window.to_tcl()
    assert isinstance(widget_path, str)

    assert teek.Window.from_tcl(widget_path) is window
    assert teek.Widget.from_tcl(widget_path) is window

    with pytest.raises(TypeError) as error:
        teek.Label.from_tcl(widget_path)
    assert str(error.value).endswith(" is a Window, not a Label")


@pytest.mark.skipif(teek.TK_VERSION < (8, 6), reason="busy is new in Tk 8.6")
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
    class Asd(teek.Label):
        pass

    AsdLabel = Asd

    class Asd(teek.Button):
        pass

    AsdButton = Asd

    # it must not be possible to have two Asds with same to_tcl() widget path,
    window = teek.Window()
    label = AsdLabel(window)
    button = AsdButton(window)

    while get_counter_value(label) < get_counter_value(button):
        label = AsdLabel(window)
        assert label.to_tcl() != button.to_tcl()

    while get_counter_value(button) < get_counter_value(label):
        button = AsdButton(window)
        assert label.to_tcl() != button.to_tcl()


def test_winfo_ismapped():
    window = teek.Window()
    teek.update()
    assert window.winfo_ismapped() is True

    frame = teek.Frame(window)
    assert frame.winfo_ismapped() is False
    teek.update()
    assert frame.winfo_ismapped() is False

    frame.pack()
    teek.update()
    assert frame.winfo_ismapped() is True


def test_winfo_x_y_rootx_rooty_width_height_reqwidth_reqheight():
    # layout in the window looks like this:
    #     ________
    #    |        |
    #    |        |
    #    |        |
    #    |        |456px
    #    |        |
    #    |        |
    #    |________|___
    #      123px  | a |
    #             `---'
    window = teek.Window()
    spacer = teek.Frame(window, width=123, height=456)
    spacer.grid(row=1, column=1)
    label = teek.Label(window, text='a')
    label.grid(row=2, column=2)
    window.geometry(100, 200)
    teek.update()

    assert window.toplevel.winfo_x() == window.toplevel.winfo_rootx()
    assert window.toplevel.winfo_y() == window.toplevel.winfo_rooty()
    assert window.toplevel.winfo_width() == 100
    assert window.toplevel.winfo_height() == 200
    assert window.toplevel.winfo_reqwidth() > 123
    assert window.toplevel.winfo_reqheight() > 456

    assert spacer.winfo_x() == 0
    assert spacer.winfo_y() == 0
    assert spacer.winfo_rootx() == window.toplevel.winfo_x()
    assert spacer.winfo_rooty() == window.toplevel.winfo_y()
    assert spacer.winfo_width() == 123
    assert spacer.winfo_height() == 456
    assert spacer.winfo_reqwidth() == 123
    assert spacer.winfo_reqheight() == 456

    assert label.winfo_x() == 123
    assert label.winfo_y() == 456
    assert label.winfo_rootx() == window.toplevel.winfo_x() + 123
    assert label.winfo_rooty() == window.toplevel.winfo_y() + 456
    assert label.winfo_width() > 0
    assert label.winfo_height() > 0
    assert label.winfo_reqwidth() > 0
    assert label.winfo_reqheight() > 0


def test_winfo_id():
    window = teek.Window()
    frame1 = teek.Frame(window)
    frame2 = teek.Frame(window)
    assert isinstance(frame1.winfo_id(), int)
    assert frame1.winfo_id() == frame1.winfo_id()
    assert frame1.winfo_id() != frame2.winfo_id()


def test_focus(fake_command):
    widget = teek.Window()

    with fake_command('focus') as called:
        widget.focus()
        widget.focus(force=True)
        assert called == [
            [widget.to_tcl()],
            ['-force', widget.to_tcl()],
        ]


def test_state():
    assert teek.Menu().state is None
    assert teek.Toplevel().state is None

    state = teek.Button(teek.Window()).state
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
