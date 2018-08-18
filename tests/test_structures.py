import pythotk as tk

import pytest


def test_callbacks(capsys):
    result1 = []
    result2 = []

    cb = tk.Callback(str)
    cb.connect(result1.append)
    cb.connect(result1.append)   # repeated intentionally
    cb.connect(result2.append)

    with pytest.raises(TypeError) as error:
        cb.run(123)
    assert str(error.value) == "should be run(str), not run(int)"

    with pytest.raises(TypeError) as error:
        cb.run("hello", "world")
    assert str(error.value) == "should be run(str), not run(str, str)"

    with pytest.raises(TypeError) as error:
        cb.run(123)
    assert str(error.value) == "should be run(str), not run(int)"

    cb.run('lol')
    assert result1 == ['lol', 'lol']
    assert result2 == ['lol']
    result1.clear()
    result2.clear()

    cb.disconnect(result1.append)
    cb.run('wut')
    assert result1 == result2 == ['wut']
    result1.clear()
    result2.clear()

    cb.disconnect(result1.append)
    cb.disconnect(result2.append)
    cb.run('wat wat')
    assert result1 == result2 == []

    with pytest.raises(ValueError):
        cb.disconnect(result1)

    assert capsys.readouterr() == ('', '')

    def broken_callback(whatever):
        1 / 0

    cb.connect(broken_callback)
    cb.run('wat')         # doesn't raise an error
    output, errors = capsys.readouterr()
    assert not output
    assert 'cb.connect(broken_callback)' in errors


# most things are tested with doctests, but this is for testing corner cases
def test_colors():
    # these must work
    tk.Color(1, 2, 255)
    tk.Color(1, 2, 0)

    with pytest.raises(ValueError):
        tk.Color(1, 2, 256)
    with pytest.raises(ValueError):
        tk.Color(1, 2, -1)
    with pytest.raises(TypeError):
        tk.Color(1, 2, 3, 4)
    with pytest.raises(TypeError):
        tk.Color()

    blue1 = tk.Color(0, 0, 255)
    blue2 = tk.Color('blue')
    white = tk.Color('white')

    assert repr(blue1).startswith("<Color '#0000ff': ")
    assert repr(blue2).startswith("<Color 'blue': ")
    assert blue1 == blue2
    assert blue1 != 'Woot Woot!'
    assert hash(blue1) == hash(blue2)
    assert hash(blue1) != hash(white)

    the_dict = {blue1: 'hi'}
    assert the_dict[blue1] == 'hi'
    assert the_dict[blue2] == 'hi'   # __hash__ works correctly
    with pytest.raises(KeyError):
        the_dict[white]
