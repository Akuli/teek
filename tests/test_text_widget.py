import itertools
import os

import pytest

import pythotk as tk


def test_basic_stuff():
    text = tk.Text(tk.Window())

    # start and end should be namedtuples
    assert isinstance(text.start, tuple)
    assert type(text.start) is not tuple

    # there is nothing in the text widget yet
    assert text.start == text.end == (1, 0)

    text.insert(text.end, 'this is some text\nbla bla bla')
    assert text.get(text.start, text.end) == 'this is some text\nbla bla bla'
    assert text.start == (1, 0)
    assert text.end == (2, 11)
    assert 'contains 2 lines of text' in repr(text)

    text.replace((1, 0), (1, 4), 'lol')
    assert text.get(text.start, text.end) == 'lol is some text\nbla bla bla'

    assert text.get((1, 0), (1, 6)) == 'lol is'
    assert text.get((1, 12), (2, 3)) == 'text\nbla'

    assert text.get() == text.get(text.start, text.end)
    assert text.get(text.start) == text.get(text.start, text.end)

    assert text.start.forward(chars=2, lines=1) == (2, 2)
    assert (text.start.forward(chars=2, lines=1).back(chars=2, lines=1) ==
            text.start)
    assert text.start.forward(chars=100) == text.end

    assert text.start.wordend() == (1, 3)               # after 'lol'
    assert text.start.wordend().linestart() == text.start
    assert (text.start.wordend().lineend() ==
            text.start.forward(lines=1).back(chars=1))

    # Tk's wordstart() seems to be funny, so this is the best test i came
    # up with
    assert text.start.wordstart() == text.start

    # indexes compare nicelys
    assert (text.start <
            text.start.forward(chars=1) <
            text.start.forward(lines=1) <
            text.start.forward(chars=1, lines=1))


# see text(3tk) with different tk versions
def test_config_types(check_config_types):
    text = tk.Text(tk.Window())
    check_config_types(text.config, 'Text')
    check_config_types(text.get_tag('asdfasdf'), 'Text tag')


def test_tags():
    text = tk.Text(tk.Window())
    text.insert(text.start, "asd toot boo")

    assert {tag.name for tag in text.get_all_tags()} == {'sel'}
    assert text.get_tag('asd').name == 'asd'

    # do any tag Tcl call that ensures the asd tag exists
    text.get_tag('asd')['foreground']

    assert {tag.name for tag in text.get_all_tags()} == {'sel', 'asd'}

    for tag in [text.get_tag('asd'), text.get_tag('sel')]:
        assert tag is text.get_tag(tag.name)  # returns same tag obj every time

        tag.add((1, 4), (1, 8))
        assert tag.ranges() == [((1, 4), (1, 8))]
        flatten = itertools.chain.from_iterable
        assert all(isinstance(index, type(text.start))
                   for index in flatten(tag.ranges()))

        assert tag.nextrange((1, 0)) == ((1, 4), (1, 8))
        assert tag.nextrange((1, 0), (1, 4)) is None
        for index in tag.nextrange((1, 0)):
            assert isinstance(index, type(text.start))

        tag.remove()
        assert tag.ranges() == []

    # all tags must have the same options
    option_frozensets = set()
    for tag in text.get_all_tags():
        option_frozensets.add(frozenset(tag.keys()))
    assert len(option_frozensets) == 1      # they are unique

    # because nothing else covers this
    assert len(text.get_tag('asd')) == len(list(option_frozensets)[0])

    toot = text.get_tag('toot')
    toot.add((1, 4), text.end)
    assert toot.ranges() != []
    toot.delete()
    assert toot not in text.get_all_tags()
    assert toot.ranges() == []
    assert toot not in text.get_all_tags()

    # if it's set to a string, it must still be a Color object when getting
    toot['foreground'] = 'black'
    assert toot in text.get_all_tags()
    assert isinstance(toot['foreground'], tk.Color)
    assert toot['foreground'] == tk.Color(0, 0, 0)

    toot['foreground'] = tk.Color('blue')
    assert toot['foreground'] == tk.Color('blue')

    # misc other tag properties
    assert toot == toot
    assert toot != tk.Text(tk.Window()).get_tag('toot')   # different widget
    assert toot != 123
    assert hash(toot) == hash(toot)
    assert repr(toot) == "<Text widget tag 'toot'>"
    with pytest.raises(TypeError):
        del toot['foreground']

    tag_names = {'sel', 'asd', 'toot'}
    for tag_name in tag_names:
        text.get_tag(tag_name).add((1, 4), (1, 8))
    assert {tag.name for tag in text.get_all_tags((1, 6))} == tag_names


def test_marks():
    text = tk.Text(tk.Window())
    assert text.marks.keys() == {'insert', 'current'}
    assert text.marks['insert'] == text.start
    assert text.marks['current'] == text.start

    text.insert(text.start, 'hello world')
    text.marks['before space'] = text.start.forward(chars=5)
    assert text.marks['before space'] == text.start.forward(chars=5)
    del text.marks['before space']
    assert 'before space' not in text.marks


def test_scrolling():
    text = tk.Text(tk.Window())
    asd = []

    def callback(x, y):
        asd.extend([x, y])

    text.config['yscrollcommand'].connect(callback)
    text.insert(text.end, 'toot\ntoot\n' * text.config['height'])

    # scroll to end, and make sure everything is visible
    text.yview('moveto', 1)
    text.pack()
    tk.update()

    # this fails consistently in travis for some reason, but if i run this
    # locally in xvfb-run, it works fine 0_o
    if 'CI' not in os.environ:
        assert round(asd[-2], 1) == 0.5
        assert asd[-1] == 1.0

    # yview return type checks
    assert text.yview('moveto', 1) is None
    pair = text.yview()
    assert isinstance(pair, tuple) and len(pair) == 2
    assert all(isinstance(item, float) for item in pair)
