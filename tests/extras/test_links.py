import functools
import webbrowser

import pythotk as tk
from pythotk.extras import links


def test_links_clicking():
    text = tk.Text(tk.Window())

    stuff = []
    links.add_function_link(
        text, 'abc', functools.partial(stuff.append, 1))
    links.add_function_link(
        text, '123', functools.partial(stuff.append, 2), (1, 2))
    assert text.get() == 'ab123c'

    all_tag_names = (tag.name for tag in text.get_all_tags())
    assert {'pythotk-extras-link-1',
            'pythotk-extras-link-2',
            'pythotk-extras-link-common'}.issubset(all_tag_names)

    text.get_tag('pythotk-extras-link-1').bindings['<1>'].run(None)
    text.get_tag('pythotk-extras-link-2').bindings['<1>'].run(None)
    assert stuff == [1, 2]


def test_links_cursor_changes():
    text = tk.Text(tk.Window())
    text.config['cursor'] = 'clock'

    links.add_function_link(text, 'abc', print)
    assert text.config['cursor'] == 'clock'

    for binding, cursor in [('<Leave>', 'clock'),
                            ('<Enter>', 'hand2'),
                            ('<Leave>', 'clock')]:
        text.get_tag('pythotk-extras-link-common').bindings[binding].run(None)
        assert text.config['cursor'] == cursor


URL = 'https://github.com/Akuli/pythotk'


def test_add_url_link(monkeypatch, handy_callback):
    stuff = []
    monkeypatch.setattr(webbrowser, 'open', stuff.append)

    text = tk.Text(tk.Window())
    links.add_url_link(text, 'asd', URL)
    text.get_tag('pythotk-extras-link-1').bindings['<1>'].run(None)
    assert stuff == [URL]
