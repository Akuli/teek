from functools import partial
import os

import teek


def _options(kwargs):
    if 'parent' in kwargs and isinstance(kwargs['parent'], teek.Window):
        kwargs['parent'] = kwargs['parent'].toplevel

    for name, value in kwargs.items():
        yield '-' + name
        yield value


def color(**kwargs):
    """Calls :man:`tk_chooseColor(3tk)`.

    The color selected by the user is returned, or ``None`` if the user
    cancelled the dialog.
    """
    return teek.tcl_call(teek.Color, 'tk_chooseColor', *_options(kwargs))


def _messagebox(type, title, message, detail=None, **kwargs):
    kwargs['type'] = type
    kwargs['title'] = title
    kwargs['message'] = message
    if detail is not None:
        kwargs['detail'] = detail

    if type == 'ok':
        teek.tcl_call(None, 'tk_messageBox', *_options(kwargs))
        return None
    if type == 'okcancel':
        return teek.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'ok'
    if type == 'retrycancel':
        return (
            teek.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'retry')
    if type == 'yesno':
        return teek.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'yes'

    # for anything else, return a string
    return teek.tcl_call(str, 'tk_messageBox', *_options(kwargs))


info = partial(_messagebox, 'ok', icon='info')
warning = partial(_messagebox, 'ok', icon='warning')
error = partial(_messagebox, 'ok', icon='error')
ok_cancel = partial(_messagebox, 'okcancel', icon='question')
retry_cancel = partial(_messagebox, 'retrycancel', icon='warning')
yes_no = partial(_messagebox, 'yesno', icon='question')
yes_no_cancel = partial(_messagebox, 'yesnocancel', icon='question')
abort_retry_ignore = partial(_messagebox, 'abortretryignore', icon='error')


def _check_multiple(kwargs):
    if 'multiple' in kwargs:
        raise TypeError(
            "the 'multiple' option is not supported, use open_file() or "
            "open_multiple_files() depending on whether you want to support "
            "selecting multiple files at once")


def open_file(**kwargs):
    """
    Ask the user to choose an existing file. Returns the path.

    This calls :man:`tk_getOpenFile(3tk)` without ``-multiple``. ``None`` is
    returned if the user cancels.
    """
    _check_multiple(kwargs)
    result = teek.tcl_call(str, 'tk_getOpenFile', *_options(kwargs))
    if not result:
        return None
    return os.path.abspath(result)


def open_multiple_files(**kwargs):
    """
    Ask the user to choose one or more existing files. Returns a list of paths.

    This calls :man:`tk_getOpenFile(3tk)` with ``-multiple`` set to true. An
    empty list is returned if the user cancels.
    """
    _check_multiple(kwargs)
    result = teek.tcl_call(
        [str], 'tk_getOpenFile', '-multiple', True, *_options(kwargs))
    return list(map(os.path.abspath, result))


def save_file(**kwargs):
    """Ask the user to choose a path for a new file. Return the path.

    This calls :man:`tk_getSaveFile(3tk)`, and returns ``None`` if the user
    cancels.
    """
    result = teek.tcl_call(str, 'tk_getSaveFile', *_options(kwargs))
    if not result:
        return None
    return os.path.abspath(result)


def directory(**kwargs):
    """Asks the user to choose a directory, and return a path to it.

    This calls :man:`tk_chooseDirectory(3tk)`, and returns ``None`` if the user
    cancels.

    .. note::
        By default, the user can choose a directory that doesn't exist yet.
        This behaviour is documented in :man:`tk_chooseDirectory(3tk)`. If you
        want the user to choose an existing directory, use ``mustexist=True``.
    """
    result = teek.tcl_call(str, 'tk_chooseDirectory', *_options(kwargs))
    if not result:
        return None
    return os.path.abspath(result)
