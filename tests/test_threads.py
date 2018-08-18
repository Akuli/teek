import functools
import re
import threading
import traceback

import pytest

import pythotk as tk


def test_basic_stuff(deinit_threads):
    tk.init_threads()
    text = tk.Text(tk.Window())

    def thread_target():
        for i in (1, 2, 3):
            text.insert(text.end, 'hello %d\n' % i)

    thread = threading.Thread(target=thread_target)
    thread.start()

    ran = 0

    def done_callback():
        assert text.get(text.start, text.end) == 'hello 1\nhello 2\nhello 3\n'
        tk.quit()

        nonlocal ran
        ran += 1

    # i experimented with different values: on my system 1000 was enough, but
    # 900 was too small, so this should be plenty
    #
    # ik, it's ridiculously slow, i should add a context manager for repeated
    # calls like in thread_target()
    tk.after(2000, done_callback)
    tk.run()
    thread.join()
    assert ran == 1


def test_init_threads_errors(deinit_threads):
    ran = 0

    def thread_target():
        with pytest.raises(RuntimeError) as error:
            tk.init_threads()
        assert (str(error.value) ==
                "init_threads() must be called from main thread")

        for cb in [functools.partial(tk.call, None, 'puts', 'hello'),
                   functools.partial(tk.eval, None, 'puts hello')]:
            with pytest.raises(RuntimeError) as error:
                cb()
            assert str(error.value) == "init_threads() wasn't called"

        nonlocal ran
        ran += 1

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert ran == 1

    tk.init_threads()
    with pytest.raises(RuntimeError) as error:
        tk.init_threads()
    assert str(error.value) == "init_threads() was called twice"


def test_run_called_from_wrong_thread():
    ran = 0

    def thread_target():
        with pytest.raises(RuntimeError) as error:
            tk.run()
        assert str(error.value) == "run() must be called from main thread"

        nonlocal ran
        ran += 1

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert ran == 1


def test_error_in_thread_call(deinit_threads):
    tk.init_threads()
    ran = 0

    def thread_target():
        with pytest.raises(tk.TclError) as error:
            tk.eval(None, "expr {1/0}")

        exc = error.value
        assert isinstance(exc, tk.TclError)
        assert exc.__traceback__ is not None

        # error_message is the traceback that python would display if this
        # error wasn't caught
        error_message = ''.join(traceback.format_exception(
            type(exc), exc, exc.__traceback__))
        assert error_message.startswith("Traceback (most recent call last):\n")

        regex = (r'\n'
                 r'  File ".*test_threads\.py", line \d+, in thread_target\n'
                 r'    tk\.eval\(None, "expr {1/0}"\)\n')
        assert re.search(regex, error_message) is not None

        nonlocal ran
        ran += 1

    thread = threading.Thread(target=thread_target)
    thread.start()
    tk.after(100, tk.quit)
    tk.run()
    thread.join()
    assert ran == 1