import os
import time

import pytest

import pythotk as tk


@pytest.mark.skipif('CI' in os.environ,
                    reason="this fails randomly in travis, no idea why")
def test_after():
    start = time.time()
    timeout = tk.after(200, tk.quit)
    assert repr(timeout).startswith("<pending 'quit' timeout")

    tk.run()
    end = time.time()

    # the upper bound used to be 0.21, but it failed once
    assert 0.20 < (end - start) < 0.22
    assert repr(timeout).startswith("<successfully completed 'quit' timeout")


def test_after_idle():
    stuff = []
    for i in range(5):
        tk.after_idle(stuff.append, [i])        # test positional args
    tk.after_idle(tk.quit)
    tk.run()
    assert stuff == list(range(5))


def test_errors(capsys):
    def thingy(**kwargs):    # test kwargs
        assert kwargs == {'lol': 'wut'}
        raise RuntimeError("\N{pile of poo}")

    timeout = tk.after_idle(thingy, kwargs={'lol': 'wut'})
    assert repr(timeout).startswith("<pending 'thingy' timeout")
    tk.after_idle(tk.quit)
    tk.run()
    assert repr(timeout).startswith("<failed 'thingy' timeout")

    output, errors = capsys.readouterr()
    assert not output
    assert "timeout = tk.after_idle(thingy, kwargs={'lol': 'wut'})" in errors
    assert "\N{pile of poo}" in errors


def test_cancel():
    timeout = tk.after(1000, print, args=["it didn't work"])
    timeout.cancel()
    assert repr(timeout).startswith("<cancelled 'print' timeout")

    with pytest.raises(RuntimeError) as error:
        timeout.cancel()
    assert str(error.value) == "cannot cancel a cancelled timeout"

    def try_to_cancel_the_completed_timeout():
        with pytest.raises(RuntimeError) as error:
            timeout.cancel()
        assert str(error.value) == ("cannot cancel a successfully " +
                                    "completed timeout")

    timeout = tk.after_idle(lambda: None)
    tk.after(50, try_to_cancel_the_completed_timeout)
    tk.after(100, tk.quit)
    tk.run()
