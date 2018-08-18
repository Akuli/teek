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
    command = tk.create_command(result.append, ['hello'])
    tk.eval(None, command)
    assert result == ['hello']

    tk.delete_command(command)
    with pytest.raises(tk.TclError):
        tk.eval(None, command)


@pytest.fixture
def handy_commands():
    tk.eval(None, 'proc returnArg {arg} { return $arg }')
    tk.eval(None, 'proc returnEmptyString {} {}')
    yield
    tk.delete_command('returnArg')
    tk.delete_command('returnEmptyString')


def test_eval_and_call(handy_commands):
    assert tk.eval(None, 'if {1 == 2} {puts omg}') is None
    assert tk.eval(str, 'list a b c') == 'a b c'
    assert tk.eval(int, 'expr 22 / 7') == 3
    assert round(tk.eval(float, 'expr 22 / 7.0'), 2) == 3.14
    assert tk.eval([int], 'list 1 2 3') == [1, 2, 3]
    assert tk.eval([str], 'list { a} {b } { c }') == [' a', 'b ', ' c ']
    assert tk.eval((str, int, str, int), 'list a 1 b 2') == ('a', 1, 'b', 2)
    assert tk.eval(
        {'a': int, 'c': bool}, 'dict create a 1 b 2') == {'a': 1, 'b': '2'}

    with pytest.raises(ValueError):
        tk.eval(int, 'returnArg lel')
    with pytest.raises(ValueError):
        tk.eval((str, str), 'list a b c')
    with pytest.raises(ValueError):
        tk.eval([int], 'list 1 2 3 yay')

    bools = ['true false', 'tru fal', 'yes no', 'y n', 'on off', '1 0']
    for yes, no in map(str.split, bools):
        assert tk.call(bool, 'returnArg', yes.upper()) is True
        assert tk.call(bool, 'returnArg', no.upper()) is False
        assert tk.call(bool, 'returnArg', yes.lower()) is True
        assert tk.call(bool, 'returnArg', no.lower()) is False
    assert tk.eval(bool, 'returnEmptyString') is None

    with pytest.raises(ValueError):
        tk.eval(bool, 'returnArg lolwut')

    with pytest.raises(TypeError):
        tk.call(None, 'puts', object())
    with pytest.raises(TypeError):
        tk.eval(object(), 'puts hello')

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
        assert tk.call(str, 'concat', before) == after
        assert tk.call(str, 'concat', 'blah', before) == 'blah ' + after

    # test conversion to strings when tk.calling
    assert tk.call(
        str, 'list', True, 5, 3.14, [1, 2], {3: 4}, ('lol', 'wut'),
    ) == '1 5 3.14 {1 2} {3 4} {lol wut}'


def test_create_command(capsys):
    def working_func():
        # no type checking is done, this turns into a dict below
        return CustomSequence()

    command = tk.create_command(working_func)
    assert tk.call({'a b c': int}, command) == {'a b c': 123}
    assert capsys.readouterr() == ('', '')

    def broken_func(arg1, *, arg2):
        if arg1 == 'one' and arg2 == 'two':
            print('it works')
        else:
            print('it doesnt work :( arg1=%r arg2=%r' % (arg1, arg2))
        raise RuntimeError("oh noes")

    command = tk.create_command(broken_func, ['one'], {'arg2': 'two'})
    assert tk.call(str, command) == ''

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors

    def create_the_command():
        stack_info = traceback.format_stack()[-2]
        return tk.create_command(broken_func, ['one'], {'arg2': 'two'},
                                 stack_info=stack_info)

    command = create_the_command()
    assert tk.call(str, command) == ''

    output, errors = capsys.readouterr()
    assert output == 'it works\n'
    assert 'raise RuntimeError("oh noes")' in errors
    assert 'command = create_the_command()' in errors

    # test return values
    def lel():
        return (True, 3, ['a', 'b', 'c'])

    command = tk.create_command(lel)
    assert tk.call((bool, int, [str]), command) == (True, 3, ['a', 'b', 'c'])


class NonHashableCallable:
    __hash__ = None

    def __call__(self):
        pass


def test_callback_cache(capsys):
    assert (tk.create_command(print) !=
            tk.create_command(print, args=['hello']) !=
            tk.create_command(print, kwargs={'sep': '-'}) !=
            tk.create_command(print, stack_info='lol'))
    assert tk.create_command(print) == tk.create_command(print)

    assert (tk.create_command(print, args=[{'lel'}]) !=
            tk.create_command(print, args=[{'lel'}]))

    func = NonHashableCallable()
    assert tk.create_command(func) != tk.create_command(func)
