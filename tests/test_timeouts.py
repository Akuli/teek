import os
import time

import pytest

import teek


@pytest.mark.slow
@pytest.mark.skipif('CI' in os.environ,
                    reason="this fails randomly in travis, no idea why")
def test_after():
    start = time.time()
    timeout = teek.after(200, teek.quit)
    assert repr(timeout).startswith("<pending 'quit' timeout")

    teek.run()
    end = time.time()

    # the upper bound used to be 0.21, but it failed once
    # then i tried 0.22 and after a while that failed too
    assert 0.20 < (end - start) < 0.25
    assert repr(timeout).startswith("<successfully completed 'quit' timeout")


def test_after_idle():
    stuff = []
    for i in range(5):
        teek.after_idle(stuff.append, [i])        # test positional args
    teek.after_idle(teek.quit)
    teek.run()
    assert stuff == list(range(5))


def test_errors(capsys):
    def thingy(**kwargs):    # test kwargs
        assert kwargs == {'lol': 'wut'}
        raise RuntimeError("\N{pile of poo}")

    timeout = teek.after_idle(thingy, kwargs={'lol': 'wut'})
    assert repr(timeout).startswith("<pending 'thingy' timeout")
    teek.after_idle(teek.quit)
    teek.run()
    assert repr(timeout).startswith("<failed 'thingy' timeout")

    output, errors = capsys.readouterr()
    assert not output
    assert "timeout = teek.after_idle(thingy, kwargs={'lol': 'wut'})" in errors
    assert "\N{pile of poo}" in errors


def test_cancel():
    timeout = teek.after(1000, print, args=["it didn't work"])
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

    timeout = teek.after_idle(lambda: None)
    teek.after(50, try_to_cancel_the_completed_timeout)
    teek.after(100, teek.quit)
    teek.run()
