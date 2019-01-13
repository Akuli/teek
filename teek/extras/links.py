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


def add_function_link(textwidget, text, function, index=None):
    """
    Like :func:`add_url_link`, but calls a function instead of opening a URL
    in a web browser.
    """
    if index is None:
        index = textwidget.end

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
    textwidget.insert(index, text, [common_tag, specific_tag])


def add_url_link(textwidget, text, url, index=None):
    """Adds ``text`` to ``textwidget`` so that clicking it will open ``url``.

    By default, the text is added to the end of the text widget, but you can
    use ``index`` to specify a different :ref:`text index <textwidget-index>`.
    """
    add_function_link(textwidget, text,
                      functools.partial(webbrowser.open, url), index)
