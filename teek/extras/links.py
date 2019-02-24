import functools
import webbrowser

_TAG_PREFIX = 'teek-extras-link-'


def _init_links(widget):
    if _TAG_PREFIX + 'common' in (tag.name for tag in widget.get_all_tags()):
        return widget.get_tag(_TAG_PREFIX + 'common')

    old_cursor = widget.config['cursor']

    def enter():
        nonlocal old_cursor
        old_cursor = widget.config['cursor']
        widget.config['cursor'] = 'hand2'

    def leave():
        widget.config['cursor'] = old_cursor

    tag = widget.get_tag(_TAG_PREFIX + 'common')
    tag['foreground'] = 'blue'
    tag['underline'] = True
    tag.bind('<Enter>', enter)
    tag.bind('<Leave>', leave)
    return tag


def add_function_link(textwidget, function, start, end):
    """
    Like :func:`add_url_link`, but calls a function instead of opening a URL
    in a web browser.
    """
    common_tag = _init_links(textwidget)

    names = {tag.name for tag in textwidget.get_all_tags()}
    i = 1
    while _TAG_PREFIX + str(i) in names:
        i += 1
    specific_tag = textwidget.get_tag(_TAG_PREFIX + str(i))

    # bind callbacks must return None or 'break', but this ignores the
    # function's return value
    def none_return_function():
        function()

    specific_tag.bind('<Button-1>', none_return_function)
    for tag in [common_tag, specific_tag]:
        tag.add(start, end)


def add_url_link(textwidget, url, start, end):
    """
    Make some of the text in the textwidget to be clickable so that clicking
    it will open ``url``.

    The text between the :ref:`text indexes <textwidget-index>` ``start`` and
    ``end`` becomes clickable, and rest of the text is not touched.

    Do this if you want to insert some text and make it a link immediately::

        from teek.extras import links

        ...

        old_end = textwidget.end    # adding text to end changes textwidget.end
        textwidget.insert(textwidget.end, 'Click me')
        links.add_url_link(textwidget, 'https://example.com/', old_end, textwi\
dget.end)

    This function uses :func:`webbrowser.open` for opening ``url``.
    """
    add_function_link(textwidget, functools.partial(webbrowser.open, url),
                      start, end)
