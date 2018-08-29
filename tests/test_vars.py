import functools
import time

import pytest

import pythotk as tk


def test_basic_stuff():
    var = tk.TclVar()
    var.set('asd')
    assert var.get() == 'asd'

    var.type = [int]
    var.set([1, 2])
    assert var.get() == [1, 2]


def test_write_trace(handy_callback):
    @handy_callback
    def tracer(value):
        assert value == [1, 2, 3]

    var = tk.TclVar(type=[int])
    assert var.write_trace is var.write_trace
    var.write_trace.connect(tracer)
    var.set([1, 2, 3])
    assert tracer.ran_once()


def test_creating_var_objects_from_name():
    asd = []
    var = tk.TclVar()
    var.write_trace.connect(asd.append)
    var.set('a')
    tk.TclVar(name=var.to_tcl()).set('b')
    tk.TclVar.from_tcl(var.to_tcl()).set('c')
    assert asd == ['a', 'b', 'c']


def test_repr():
    var = tk.TclVar(name='testie_var')
    assert repr(var) == "<TclVar 'testie_var': no value has been set>"
    var.set('asd')
    assert repr(var) == "<TclVar 'testie_var': 'asd'>"


@pytest.mark.slow
def test_wait():
    var = tk.TclVar()
    start = time.time()
    tk.after(500, functools.partial(var.set, "boo"))
    var.wait()          # should run the event loop ==> after callback works
    end = time.time()
    assert (end - start) > 0.5
