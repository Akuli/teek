import collections.abc
import platform

import pytest

import teek


# tkinter only handles lists and tuples, not things like this
class CustomSequence(collections.abc.Sequence):

    def __getitem__(self, index):
        if index not in (0, 1):
            raise IndexError
        return 'a b c' if index == 0 else '123'

    def __len__(self):
        return 2


def test_delete_command():
    result = []
    command = teek.create_command(result.append, [int])
    teek.tcl_call(None, command, '123')
    assert result == [123]

    teek.delete_command(command)
    with pytest.raises(teek.TclError):
        teek.tcl_call(None, command, '123')


@pytest.fixture
def handy_commands():
    teek.tcl_eval(None, 'proc returnArg {arg} { return $arg }')
    teek.tcl_eval(None, 'proc returnEmptyString {} {}')
    yield
    teek.delete_command('returnArg')
    teek.delete_command('returnEmptyString')


def test_eval_and_call(handy_commands, capfd):
    assert teek.tcl_eval(None, 'if {1 == 2} {puts omg}') is None
    assert teek.tcl_eval(str, 'list a b c') == 'a b c'
    assert teek.tcl_eval(int, 'expr 22 / 7') == 3
    assert teek.tcl_eval(int, 'returnEmptyString') is None
    assert round(teek.tcl_eval(float, 'expr 22 / 7.0'), 2) == 3.14
    assert teek.tcl_eval([int], 'list 1 2 3') == [1, 2, 3]
    assert teek.tcl_eval([str], 'list { a} {b } { c }') == [' a', 'b ', ' c ']
    assert (teek.tcl_eval((str, int, str, int), 'list a 1 b 2') ==
            ('a', 1, 'b', 2))
    assert teek.tcl_eval([int], 'list 0b11111111 0o377 0xff') == [255] * 3
    assert teek.tcl_eval(
        {'a': int, 'c': bool}, 'dict create a 1 b 2') == {'a': 1, 'b': '2'}

    with pytest.raises(ValueError):
        teek.tcl_eval(int, 'returnArg lel')
    with pytest.raises(ValueError):
        teek.tcl_eval((str, str), 'list a b c')
    with pytest.raises(ValueError):
        teek.tcl_eval([int], 'list 1 2 3 yay')

    bools = ['true false', 'tru fal', 'yes no', 'y n', 'on off', '1 0']
    for yes, no in map(str.split, bools):
        assert teek.tcl_call(bool, 'returnArg', yes.upper()) is True
        assert teek.tcl_call(bool, 'returnArg', no.upper()) is False
        assert teek.tcl_call(bool, 'returnArg', yes.lower()) is True
        assert teek.tcl_call(bool, 'returnArg', no.lower()) is False
    assert teek.tcl_eval(bool, 'returnEmptyString') is None

    with pytest.raises(ValueError):
        teek.tcl_eval(bool, 'returnArg lolwut')

    with pytest.raises(TypeError):
        teek.tcl_call(None, 'puts', object())

    assert capfd.readouterr() == ('', '')
    with pytest.raises(TypeError):
        teek.tcl_eval(object(), 'puts hello')

    # tcl seems to use sometimes lf and sometimes crlf, lol
    output, errors = capfd.readouterr()
    assert output.replace('\r\n', '\n') == 'hello\n'
    assert not errors

    # forced to string converting relies on this
    test_data = [
        ('ab', 'ab'),
        ('a b', 'a b'),
        (['a', 'b'], 'a b'),
        ([' a', 'b '], '{ a} {b }'),
        (['a ', ' b'], '{a } { b}'),
        (['a', 'b c'], 'a {b c}'),
        (('a', 'b c'), 'a {b c}'),
        (CustomSequence(), '{a b c} 123'),
    ]
    for before, after in test_data:
        assert teek.tcl_call(str, 'format', '%s', before) == after

    # test conversion to strings when teek.tcl_calling
    assert teek.tcl_call(
        str, 'list', True, 5, 3.14, [1, 2], {3: 4}, ('lol', 'wut'),
    ) == '1 5 3.14 {1 2} {3 4} {lol wut}'

    # special case: Tcl empty string is None in python
    teek.tcl_eval(None, 'proc returnEmpty {} { return {} }')

    class BrokenFromTcl:

        oh_no = False

        @classmethod
        def from_tcl(cls, tcl_string):
            cls.oh_no = True
            raise RuntimeError("NO!! THIS WASNT SUPPSOED TO RUN!!!")

    assert teek.tcl_call(BrokenFromTcl, 'returnEmpty') is None
    assert not BrokenFromTcl.oh_no

    assert capfd.readouterr() == ('', '')


# this was a fun bug: tkinter returns tuples for some things, and the
# empty tuple was handled differently for some reason, but the only way
# to get tkinter to return an empty tuple i found is tk_getSaveFile when
# cancel is pressed (or the esc key, which is what this code simulates)
@pytest.mark.slow
def test_empty_tuple_bug():
    # after half a second, press escape in the widget of the dialog that
    # happens to be focused
    teek.after(500, lambda: teek.tcl_eval(
        None, "event generate [focus] <Escape>"))

    # do the dialog, tkinter should return an empty tuple which should be
    # converted to an empty string
    result = teek.tcl_call(str, 'tk_getSaveFile')     # this threw an error
    assert result == ''


def test_create_command(capsys):
    def working_func():
        # no type checking is done, this turns into a dict below
        return CustomSequence()

    command = teek.create_command(working_func)

    assert teek.tcl_call({'a b c': int}, command) == {'a b c': 123}
    assert capsys.readouterr() == ('', '')

    teek.tcl_call(None, command, 'asda')
    output, errors = capsys.readouterr()
    assert not output
    assert errors.endswith(
        "TypeError: expected 0 arguments, got 1 arguments\n")

    teek.delete_command(command)

    def broken_func(arg1):
        if arg1 == 'lol':
            print('it works')
        else:
            print('it doesnt works :(', arg1)
        raise RuntimeError("oh noes")

    command = teek.create_command(broken_func, [str])
    assert teek.tcl_call(str, command, 'lol') == ''
    teek.delete_command(command)

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors

    def create_the_command():
        return teek.create_command(broken_func, [str])

    command = create_the_command()
    assert teek.tcl_call(str, command, 'lol') == ''
    teek.delete_command(command)

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors
    assert 'command = create_the_command()' in errors
    assert 'return teek.create_command(broken_func, [str])' in errors

    # test return values
    def lel():
        return (True, 3, ['a', 'b', 'c'])

    command = teek.create_command(lel)
    assert (teek.tcl_call((bool, int, [str]), command) ==
            (True, 3, ['a', 'b', 'c']))
    teek.delete_command(command)

    assert capsys.readouterr() == ('', '')


def test_create_command_arbitrary_args(capsys, handy_callback):
    @handy_callback
    def callback(a, b, *args):
        assert a == 1
        assert isinstance(a, int)
        assert b == 'lol'
        assert list(args) == expected_args

    command = teek.create_command(callback, [int, str], extra_args_type=float)

    expected_args = [1.2, 3.4, 5.6]
    teek.tcl_call(None, command, '1', 'lol', '1.2', '3.4', '5.6')
    expected_args = []
    teek.tcl_call(None, command, '1', 'lol')
    assert callback.ran == 2

    teek.tcl_call(None, command, '1')
    output, errors = capsys.readouterr()
    assert not output
    assert errors.endswith(
        'TypeError: expected at least 2 arguments, got 1 arguments\n')


def test_before_after_quit():
    teek.tcl_eval(None, '')   # make sure that a Tcl interpreter is running

    asd = []
    teek.before_quit.connect(asd.append, args=['one'])
    teek.Menu().bind('<Destroy>', (lambda: asd.append('two')))
    teek.after_quit.connect(asd.append, args=['three'])
    teek.quit()
    assert asd == ['one', 'two', 'three']


def test_update_idletasks(fake_command):
    with fake_command('update') as called:
        teek.update(idletasks_only=True)
        assert called == [['idletasks']]


@pytest.mark.skipif(platform.python_implementation() == 'PyPy',
                    reason=("this test is fragile and stupid, "
                            "fails randomly in pypy, at least in travis"))
def test_weird_error(capfd):
    # make sure that previous tests don't mess up
    teek.after_idle(teek.quit)
    teek.run()

    # ignore anything that ended up in the stderr because previous tests
    # TODO: why is stderr SOMETIMES non-empty??
    capfd.readouterr()

    teek.create_command(print)
    # the command is intentionally not deleted
    teek.quit()
    teek.update()
    assert capfd.readouterr() == ('', '')
