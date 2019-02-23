import functools
import re
import threading
import traceback

import pytest

import teek


@pytest.mark.slow
def test_make_thread_safe(handy_callback, deinit_threads):
    @teek.make_thread_safe
    @handy_callback
    def thread_target():
        assert threading.current_thread() is threading.main_thread()

    teek.init_threads()
    thread = threading.Thread(target=thread_target)
    thread.start()

    # make_thread_safe needs teek.run to work
    teek.after(500, teek.quit)
    teek.run()

    assert not thread.is_alive()
    assert thread_target.ran_once()


@pytest.mark.slow
def test_basic_stuff(deinit_threads, handy_callback):
    teek.init_threads()
    text = teek.Text(teek.Window())

    def thread_target():
        for i in (1, 2, 3):
            text.insert(text.end, 'hello %d\n' % i)

    thread = threading.Thread(target=thread_target)
    thread.start()

    @handy_callback
    def done_callback():
        assert text.get(text.start, text.end) == 'hello 1\nhello 2\nhello 3\n'
        teek.quit()

    # i experimented with different values: 500 was enough and 450 wasn't, so
    # this should be plenty
    teek.after(1000, done_callback)
    teek.run()
    thread.join()
    assert done_callback.ran_once()


def test_init_threads_errors(deinit_threads, handy_callback):
    @handy_callback
    def thread1_target():
        # the Tcl interpreter isn't started yet, so this runs an error that is
        # not covered by the code below
        with pytest.raises(RuntimeError) as error:
            teek.tcl_eval(None, '')
        assert str(error.value) == "init_threads() wasn't called"

    thread1 = threading.Thread(target=thread1_target)
    thread1.start()
    thread1.join()
    assert thread1_target.ran_once()

    # this starts the Tcl interpreter
    teek.tcl_eval(None, '')

    @handy_callback
    def thread2_target():
        with pytest.raises(RuntimeError) as error:
            teek.init_threads()
        assert (str(error.value) ==
                "init_threads() must be called from main thread")

        for cb in [functools.partial(teek.tcl_call, None, 'puts', 'hello'),
                   functools.partial(teek.tcl_eval, None, 'puts hello')]:
            with pytest.raises(RuntimeError) as error:
                cb()
            assert str(error.value) == "init_threads() wasn't called"

    thread2 = threading.Thread(target=thread2_target)
    thread2.start()
    thread2.join()
    assert thread2_target.ran_once()

    teek.init_threads()
    with pytest.raises(RuntimeError) as error:
        teek.init_threads()
    assert str(error.value) == "init_threads() was called twice"

    teek.after_idle(teek.quit)
    teek.run()


def test_run_called_from_wrong_thread(handy_callback):
    # this starts the Tcl interpreter, we get different errors without this
    teek.tcl_eval(None, '')

    @handy_callback
    def thread_target():
        with pytest.raises(RuntimeError) as error:
            teek.run()
        assert str(error.value) == "run() must be called from main thread"

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert thread_target.ran_once()


def test_error_in_thread_call(deinit_threads, handy_callback):
    teek.init_threads()

    @handy_callback
    def thread_target():
        with pytest.raises(teek.TclError) as error:
            teek.tcl_eval(None, "expr {1/0}")

        exc = error.value
        assert isinstance(exc, teek.TclError)
        assert exc.__traceback__ is not None

        # error_message is the traceback that python would display if this
        # error wasn't caught
        error_message = ''.join(traceback.format_exception(
            type(exc), exc, exc.__traceback__))
        assert error_message.startswith("Traceback (most recent call last):\n")

        regex = (r'\n'
                 r'  File ".*test_threads\.py", line \d+, in thread_target\n'
                 r'    teek\.tcl_eval\(None, "expr {1/0}"\)\n')
        assert re.search(regex, error_message) is not None

    thread = threading.Thread(target=thread_target)
    thread.start()
    teek.after(100, teek.quit)
    teek.run()
    thread.join()
    assert thread_target.ran_once()


def test_quitting_from_another_thread(handy_callback):
    teek.init_threads()

    @handy_callback
    def thread_target():
        with pytest.raises(RuntimeError) as error:
            teek.quit()
        assert str(error.value) == "can only quit from main thread"

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    assert thread_target.ran_once()
