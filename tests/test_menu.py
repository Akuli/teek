import pythotk as tk

import pytest


def test_item_types():
    menu = tk.Menu([
        ("Click me", print),
        (),     # separator
        ("Check me", tk.BooleanVar()),
        ("Choose me or one of my friends", tk.StringVar(), "me"),
        ("Submenu", [("Click here", print)]),
        ("Different kind of submenu", tk.Menu([
            ("Click me", print),
        ])),
    ])
    assert [item.type for item in menu] == [
        'command', 'separator', 'checkbutton', 'radiobutton', 'cascade',
        'cascade']

    for submenu_item in (menu[-2], menu[-1]):
        assert submenu_item.config['menu'][0].type == 'command'


def test_menuitem_objects():
    menu = tk.Menu([
        ("Click me", print, {'activeforeground': tk.Color(1, 2, 3)}),
    ])
    assert menu[0] is not menu[0]
    assert menu[0] == menu[0]
    assert menu[0] != 'boo'
    assert {menu[0]: 'asd'}[menu[0]] == 'asd'
    assert repr(menu[0]) == "<command menu item, label='Click me'>"
    assert menu[0].config['activeforeground'] == tk.Color(1, 2, 3)


def test_repr():
    assert repr(tk.Menu([("Click me", print)] * 2)) == (
        '<pythotk.Menu widget: contains 2 items>')


def test_wrong_length_menu_item_spec():
    with pytest.raises(TypeError):
        tk.Menu().append([1, 2, 3, 4, 5])


def test_destroying_deletes_commands(handy_callback):
    @handy_callback
    def callback_func():
        pass

    menu = tk.Menu([("Click me", callback_func)])
    command_string = tk.tcl_call(str, menu, 'entrycget', 0, '-command')
    tk.tcl_call(None, command_string)
    assert callback_func.ran_once()

    menu.destroy()
    with pytest.raises(tk.TclError):
        tk.tcl_call(None, command_string)


def test_config(check_config_types):
    boolean_var = tk.BooleanVar()
    string_var = tk.StringVar()
    menu = tk.Menu([
        ("Click me", print),
        ("Check me", boolean_var),
        ("Choice A", string_var, "a"),
        ("Choice B", string_var, "b"),
        ("Choice C", string_var, "c"),
        (),
        ("Submenu", []),
    ])

    for item in menu:
        check_config_types(item.config, 'menu %s item' % item.type)

    assert isinstance(menu[0].config['command'], tk.Callback)
    menu[0].config['command'].disconnect(print)     # fails if not connected

    assert isinstance(menu[1].config['variable'], tk.BooleanVar)
    assert menu[1].config['variable'] == boolean_var

    for index in (2, 3, 4):
        assert isinstance(menu[index].config['variable'], tk.StringVar)
        assert menu[index].config['variable'] == string_var


def test_list_like_behaviour():
    menu = tk.Menu()
    menu.append(("Click me", print))
    assert len(menu) == 1
    assert menu[0].config['label'] == "Click me"

    menu[-1] = ("No, click me instead", print)
    assert len(menu) == 1
    assert menu[0].config['label'] == "No, click me instead"

    menu.insert(123, ("Last item", print))
    assert menu[-1].config['label'] == 'Last item'


def test_slicing_not_supported_errors():
    check = pytest.raises(TypeError,
                          match=r'^slicing a Menu widget is not supported$')

    menu = tk.Menu()
    with check:
        menu[:]
    with check:
        menu[:] = []
    with check:
        del menu[:]
