import contextlib
import random
import re
import time

import pythotk as tk


@contextlib.contextmanager
def fake_tcl_command(name, options, return_value):
    randomness = re.sub(r'\W', '', str(random.random()) + str(time.time()))
    temp_name = 'temporary_command_' + randomness
    ran = 0

    def callback(*args):
        assert len(args) % 2 == 0
        assert set(args[0::2]) == {'-' + key for key in options.keys()}

        for name, actual_value_string in zip(args[0::2], args[1::2]):
            expected_value = options[name.lstrip('-')]

            # http://wiki.tcl.tk/40147
            expected_value_string = tk.tcl_call(
                str, 'return', '-level', 0, expected_value)

            assert actual_value_string == expected_value_string

        nonlocal ran
        ran += 1
        return return_value

    fake_command = tk.create_command(callback, extra_args_type=str)

    # here comes the magic
    tk.tcl_call(None, 'rename', name, temp_name)
    tk.tcl_call(None, 'rename', fake_command, name)
    try:
        yield
    finally:
        tk.delete_command(name)
        tk.tcl_call(None, 'rename', temp_name, name)

    assert ran == 1


def test_color():
    with fake_tcl_command('tk_chooseColor', {}, '#ffffff'):
        assert tk.dialog.color() == tk.Color('white')

    kwargs = {
        'initialcolor': tk.Color('maroon'),
        'parent': tk.Window(),
        'title': 'toot',
    }
    with fake_tcl_command('tk_chooseColor', kwargs, '#ffffff'):
        assert tk.dialog.color(**kwargs) == tk.Color('white')

    with fake_tcl_command('tk_chooseColor', {}, ''):
        assert tk.dialog.color() is None
