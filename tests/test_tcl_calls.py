import collections.abc
import traceback

import pytest

import pythotk as tk


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
    command = tk.create_command(result.append, [int])
    tk.tcl_call(None, command, '123')
    assert result == [123]

    tk.delete_command(command)
    with pytest.raises(tk.TclError):
        tk.tcl_call(None, command, '123')


@pytest.fixture
def handy_commands():
    tk.tcl_eval(None, 'proc returnArg {arg} { return $arg }')
    tk.tcl_eval(None, 'proc returnEmptyString {} {}')
    yield
    tk.delete_command('returnArg')
    tk.delete_command('returnEmptyString')


def test_eval_and_call(handy_commands):
    assert tk.tcl_eval(None, 'if {1 == 2} {puts omg}') is None
    assert tk.tcl_eval(str, 'list a b c') == 'a b c'
    assert tk.tcl_eval(int, 'expr 22 / 7') == 3
    assert round(tk.tcl_eval(float, 'expr 22 / 7.0'), 2) == 3.14
    assert tk.tcl_eval([int], 'list 1 2 3') == [1, 2, 3]
    assert tk.tcl_eval([str], 'list { a} {b } { c }') == [' a', 'b ', ' c ']
    assert (tk.tcl_eval((str, int, str, int), 'list a 1 b 2') ==
            ('a', 1, 'b', 2))
    assert tk.tcl_eval(
        {'a': int, 'c': bool}, 'dict create a 1 b 2') == {'a': 1, 'b': '2'}

    with pytest.raises(ValueError):
        tk.tcl_eval(int, 'returnArg lel')
    with pytest.raises(ValueError):
        tk.tcl_eval((str, str), 'list a b c')
    with pytest.raises(ValueError):
        tk.tcl_eval([int], 'list 1 2 3 yay')

    bools = ['true false', 'tru fal', 'yes no', 'y n', 'on off', '1 0']
    for yes, no in map(str.split, bools):
        assert tk.tcl_call(bool, 'returnArg', yes.upper()) is True
        assert tk.tcl_call(bool, 'returnArg', no.upper()) is False
        assert tk.tcl_call(bool, 'returnArg', yes.lower()) is True
        assert tk.tcl_call(bool, 'returnArg', no.lower()) is False
    assert tk.tcl_eval(bool, 'returnEmptyString') is None

    with pytest.raises(ValueError):
        tk.tcl_eval(bool, 'returnArg lolwut')

    with pytest.raises(TypeError):
        tk.tcl_call(None, 'puts', object())
    with pytest.raises(TypeError):
        tk.tcl_eval(object(), 'puts hello')

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
        assert tk.tcl_call(str, 'concat', before) == after
        assert tk.tcl_call(str, 'concat', 'blah', before) == 'blah ' + after

    # test conversion to strings when tk.tcl_calling
    assert tk.tcl_call(
        str, 'list', True, 5, 3.14, [1, 2], {3: 4}, ('lol', 'wut'),
    ) == '1 5 3.14 {1 2} {3 4} {lol wut}'

    # special case: Tcl empty string is None in python
    tk.tcl_eval(None, 'proc returnEmpty {} { return {} }')

    class BrokenFromTcl:

        oh_no = False

        @classmethod
        def from_tcl(cls, tcl_string):
            cls.oh_no = True
            raise RuntimeError("NO!! THIS WASNT SUPPSOED TO RUN!!!")

    assert tk.tcl_call(BrokenFromTcl, 'returnEmpty') is None
    assert not BrokenFromTcl.oh_no


def test_create_command(capsys):
    def working_func():
        # no type checking is done, this turns into a dict below
        return CustomSequence()

    command = tk.create_command(working_func)

    assert tk.tcl_call({'a b c': int}, command) == {'a b c': 123}
    assert capsys.readouterr() == ('', '')

    tk.tcl_call(None, command, 'asda')
    output, errors = capsys.readouterr()
    assert not output
    assert errors.endswith("TypeError: expected 0 arguments, got 1\n")

    tk.delete_command(command)

    def broken_func(arg1):
        if arg1 == 'lol':
            print('it works')
        else:
            print('it doesnt works :(', arg1)
        raise RuntimeError("oh noes")

    command = tk.create_command(broken_func, [str])
    assert tk.tcl_call(str, command, 'lol') == ''
    tk.delete_command(command)

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors

    def create_the_command():
        stack_info = traceback.format_stack()[-2]
        return tk.create_command(broken_func, [str], stack_info=stack_info)

    command = create_the_command()
    assert tk.tcl_call(str, command) == ''
    tk.delete_command(command)

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors
    assert 'command = create_the_command()' in errors

    # test return values
    def lel():
        return (True, 3, ['a', 'b', 'c'])

    command = tk.create_command(lel)
    assert (tk.tcl_call((bool, int, [str]), command) ==
            (True, 3, ['a', 'b', 'c']))
    tk.delete_command(command)

    assert capsys.readouterr() == ('', '')
