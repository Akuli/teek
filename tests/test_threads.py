import functools
import re
import threading
import traceback

import pytest

import pythotk as tk


def test_basic_stuff(deinit_threads, handy_callback):
    tk.init_threads()
    text = tk.Text(tk.Window())

    def thread_target():
        for i in (1, 2, 3):
            text.insert(text.end, 'hello %d\n' % i)

    thread = threading.Thread(target=thread_target)
    thread.start()

    @handy_callback
    def done_callback():
        assert text.get(text.start, text.end) == 'hello 1\nhello 2\nhello 3\n'
        tk.quit()

    # i experimented with different values: 500 was enough and 450 wasn't, so
    # this should be plenty
    tk.after(1000, done_callback)
    tk.run()
    thread.join()
    assert done_callback.ran_once()


def test_init_threads_errors(deinit_threads, handy_callback):
    @handy_callback
    def thread1_target():
        # the Tcl interpreter isn't started yet, so this runs an error that is
        # not covered by the code below
        with pytest.raises(RuntimeError) as error:
            tk.tcl_eval(None, '')
        assert str(error.value) == "init_threads() wasn't called"

    thread1 = threading.Thread(target=thread1_target)
    thread1.start()
    thread1.join()
    assert thread1_target.ran_once()

    # this starts the Tcl interpreter
    tk.tcl_eval(None, '')

    @handy_callback
    def thread2_target():
        with pytest.raises(RuntimeError) as error:
            tk.init_threads()
        assert (str(error.value) ==
                "init_threads() must be called from main thread")

        for cb in [functools.partial(tk.tcl_call, None, 'puts', 'hello'),
                   functools.partial(tk.tcl_eval, None, 'puts hello')]:
            with pytest.raises(RuntimeError) as error:
                cb()
            assert str(error.value) == "init_threads() wasn't called"

    thread2 = threading.Thread(target=thread2_target)
    thread2.start()
    thread2.join()
    assert thread2_target.ran_once()

    tk.init_threads()
    with pytest.raises(RuntimeError) as error:
        tk.init_threads()
    assert str(error.value) == "init_threads() was called twice"

    tk.after_idle(tk.quit)
    tk.run()


def test_run_called_from_wrong_thread(handy_callback):
    # this starts the Tcl interpreter, we get different errors without this
    tk.tcl_eval(None, '')

    @handy_callback
    def thread_target():
        with pytest.raises(RuntimeError) as error:
            tk.run()
        assert str(error.value) == "run() must be called from main thread"

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert thread_target.ran_once()


def test_error_in_thread_call(deinit_threads, handy_callback):
    tk.init_threads()

    @handy_callback
    def thread_target():
        with pytest.raises(tk.TclError) as error:
            tk.tcl_eval(None, "expr {1/0}")

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
                 r'    tk\.tcl_eval\(None, "expr {1/0}"\)\n')
        assert re.search(regex, error_message) is not None

    thread = threading.Thread(target=thread_target)
    thread.start()
    tk.after(100, tk.quit)
    tk.run()
    thread.join()
    assert thread_target.ran_once()


def test_quitting_from_another_thread(handy_callback):
    tk.init_threads()

    @handy_callback
    def thread_target():
        with pytest.raises(RuntimeError) as error:
            tk.quit()
        assert str(error.value) == "can only quit from main thread"

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert thread_target.ran_once()
