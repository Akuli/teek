import pytest

import teek


def test_item_eq_hash_repr_fromtcl_totcl():
    canvas = teek.Canvas(teek.Window())
    rect = canvas.create_rectangle(100, 100, 200, 200)
    oval = canvas.create_oval(150, 150, 250, 250)

    assert repr(rect) == (
        '<rectangle canvas item at (100.0, 100.0, 200.0, 200.0)>')
    assert repr(oval) == '<oval canvas item at (150.0, 150.0, 250.0, 250.0)>'

    assert oval == oval
    assert rect != oval
    assert rect != 'lol wat'
    assert len({rect, oval}) == 2

    assert oval == canvas.Item.from_tcl(oval.to_tcl())
    assert hash(oval) == hash(canvas.Item.from_tcl(oval.to_tcl()))

    oval.delete()
    assert repr(oval) == '<deleted oval canvas item>'


def test_trying_2_create_item_directly():
    canvas = teek.Canvas(teek.Window())
    with pytest.raises(TypeError) as error:
        canvas.Item()
    assert str(error.value).startswith("don't create canvas.Item objects")


def test_item_config_usage():
    canvas = teek.Canvas(teek.Window())
    rect = canvas.create_rectangle(100, 100, 200, 200, dash='-')

    assert rect.config['dash'] == '-'
    assert rect.config['fill'] is None
    rect.config['fill'] = 'blue'
    assert rect.config['fill'] == teek.Color('blue')


def create_different_items(canvas):
    return [
        canvas.create_rectangle(100, 200, 300, 400),
        canvas.create_oval(100, 200, 300, 400),
        canvas.create_line(100, 200, 300, 400, 500, 600),
    ]


def test_create_different_items_util_function():
    canvas = teek.Canvas(teek.Window())
    from_method_names = {name.split('_')[1] for name in dir(canvas)
                         if name.startswith('create_')}
    from_util_func = {item.type_string
                      for item in create_different_items(canvas)}
    assert from_method_names == from_util_func


def test_config_types(check_config_types):
    canvas = teek.Canvas(teek.Window())
    check_config_types(canvas.config, 'Canvas')

    # it would be repeatitive to see the same warnings over and over again
    already_heard = set()

    for item in create_different_items(canvas):
        already_heard |= check_config_types(
            item.config, 'Canvas %s item' % item.type_string,
            ignore_list=already_heard)


def test_coords():
    canvas = teek.Canvas(teek.Window())
    oval = canvas.create_oval(150, 150, 250, 250)

    assert oval.coords == (150, 150, 250, 250)
    oval.coords = (50, 50, 100, 100.123)
    assert oval.coords == (50, 50, 100, 100.123)
    assert repr(oval) == '<oval canvas item at (50.0, 50.0, 100.0, 100.123)>'


def test_tags():
    canvas = teek.Canvas(teek.Window())
    rect = canvas.create_rectangle(100, 100, 200, 200)
    oval = canvas.create_oval(150, 150, 250, 250)

    assert list(rect.tags) == []
    assert list(oval.tags) == []
    rect.tags.add('a')
    assert list(rect.tags) == ['a']
    assert list(oval.tags) == []
    rect.tags.add('a')
    assert list(rect.tags) == ['a']
    assert list(oval.tags) == []
    rect.tags.add('b')
    assert list(rect.tags) == ['a', 'b']
    assert list(oval.tags) == []
    rect.tags.discard('b')
    assert list(rect.tags) == ['a']
    assert list(oval.tags) == []
    rect.tags.discard('b')
    assert list(rect.tags) == ['a']
    assert list(oval.tags) == []

    assert 'a' in rect.tags
    assert 'b' not in rect.tags


def test_find():
    canvas = teek.Canvas(teek.Window())
    rect = canvas.create_rectangle(150, 150, 200, 200)
    oval = canvas.create_oval(50, 50, 100, 100)

    assert canvas.find_closest(70, 70) == oval
    assert canvas.find_enclosed(40, 40, 110, 110) == [oval]
    assert canvas.find_overlapping(90, 90, 160, 160) == [rect, oval]

    assert rect.find_above() == oval
    assert oval.find_above() is None
    assert oval.find_below() == rect
    assert rect.find_below() is None
    assert canvas.find_all() == [rect, oval]

    rect.tags.add('asdf')
    assert canvas.find_withtag('asdf') == [rect]
    oval.tags.add('asdf')
    assert canvas.find_withtag('asdf') == [rect, oval]
