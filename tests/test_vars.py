import functools
import time

import pytest

import teek


class IntListVar(teek.TclVariable):
    type_spec = [int]


def test_basic_stuff():
    var = teek.IntVar()
    var.set('123')      # doesn't need to be of same type
    assert var.get() == 123

    var = IntListVar()
    var.set([1, 2])
    assert var.get() == [1, 2]


def test_eq_hash():
    stringvar1 = teek.StringVar(name='test_var')
    stringvar2 = teek.StringVar(name='test_var')
    lol = teek.StringVar(name='lol_var')
    intvar = teek.IntVar(name='test_var')

    assert stringvar1 == stringvar1
    assert stringvar1 == stringvar2
    assert stringvar1 != lol
    assert stringvar1 != intvar
    assert stringvar1 != 1234

    assert {stringvar1: 'asd'}[stringvar2] == 'asd'
    with pytest.raises(KeyError):
        {stringvar1: 'asd'}[intvar]


def test_write_trace(handy_callback):
    var = IntListVar()

    @handy_callback
    def tracer(arg):
        assert arg is var

    assert var.write_trace is var.write_trace
    var.write_trace.connect(tracer)
    var.set([1, 2, 3])
    assert tracer.ran_once()

    # nothing in write trace must break if this is done, only get() breaks
    var.set('osiadjfoaisdj')


def test_creating_var_objects_from_name():
    asd = []
    var = teek.StringVar()
    var.write_trace.connect(lambda junk: asd.append(var.get()))

    var.set('a')
    teek.StringVar(name=var.to_tcl()).set('b')
    teek.StringVar.from_tcl(var.to_tcl()).set('c')
    assert asd == ['a', 'b', 'c']


def test_repr():
    var = teek.StringVar(name='testie_var')
    assert repr(var) == "<StringVar 'testie_var': no value has been set>"
    var.set('asd')
    assert repr(var) == "<StringVar 'testie_var': 'asd'>"


@pytest.mark.slow
def test_wait():
    var = teek.StringVar()
    start = time.time()
    teek.after(500, functools.partial(var.set, "boo"))
    var.wait()          # should run the event loop ==> after callback works
    end = time.time()
    assert (end - start) > 0.5


def test_not_subclassed():
    with pytest.raises(TypeError) as error:
        teek.TclVariable()
    assert "cannot create instances of TclVariable" in str(error.value)
    assert "subclass TclVariable" in str(error.value)
    assert "'type_spec' class attribute" in str(error.value)
