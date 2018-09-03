import functools
import time

import pytest

import pythotk as tk


class IntListVar(tk.TclVariable):
    type_spec = [int]


def test_basic_stuff():
    var = tk.IntVar()
    var.set('123')      # doesn't need to be of same type
    assert var.get() == 123

    var = IntListVar()
    var.set([1, 2])
    assert var.get() == [1, 2]


def test_eq_hash():
    stringvar1 = tk.StringVar(name='test_var')
    stringvar2 = tk.StringVar(name='test_var')
    lol = tk.StringVar(name='lol_var')
    intvar = tk.IntVar(name='test_var')

    assert stringvar1 == stringvar1
    assert stringvar1 == stringvar2
    assert stringvar1 != lol
    assert stringvar1 != intvar
    assert stringvar1 != 1234

    assert {stringvar1: 'asd'}[stringvar2] == 'asd'
    with pytest.raises(KeyError):
        {stringvar1: 'asd'}[intvar]


def test_write_trace(handy_callback):
    @handy_callback
    def tracer(value):
        assert value == [1, 2, 3]

    var = IntListVar()
    assert var.write_trace is var.write_trace
    var.write_trace.connect(tracer)
    var.set([1, 2, 3])
    assert tracer.ran_once()


def test_creating_var_objects_from_name():
    asd = []
    var = tk.StringVar()
    var.write_trace.connect(asd.append)
    var.set('a')
    tk.StringVar(name=var.to_tcl()).set('b')
    tk.StringVar.from_tcl(var.to_tcl()).set('c')
    assert asd == ['a', 'b', 'c']


def test_repr():
    var = tk.StringVar(name='testie_var')
    assert repr(var) == "<StringVar 'testie_var': no value has been set>"
    var.set('asd')
    assert repr(var) == "<StringVar 'testie_var': 'asd'>"


@pytest.mark.slow
def test_wait():
    var = tk.StringVar()
    start = time.time()
    tk.after(500, functools.partial(var.set, "boo"))
    var.wait()          # should run the event loop ==> after callback works
    end = time.time()
    assert (end - start) > 0.5


def test_not_subclassed():
    with pytest.raises(TypeError) as error:
        tk.TclVariable()
    assert "cannot create instances of TclVariable" in str(error.value)
    assert "subclass TclVariable" in str(error.value)
    assert "'type_spec' class attribute" in str(error.value)
