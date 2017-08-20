import tkinder as tk

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
        1/0

    cb.connect(broken_callback)
    cb.run('wat')         # doesn't raise an error
    output, errors = capsys.readouterr()
    assert not output
    assert 'cb.connect(broken_callback)' in errors
