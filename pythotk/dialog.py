from functools import partial as _partial

import pythotk as tk


def _options(kwargs):
    if 'parent' in kwargs and isinstance(kwargs['parent'], tk.Window):
        kwargs['parent'] = kwargs['parent'].toplevel

    for name, value in kwargs.items():
        yield '-' + name
        yield value


def color(**kwargs):
    """Calls :man:`tk_chooseColor(3tk)`.

    The color selected by the user is returned, or ``None`` if the user
    cancelled the dialog.
    """
    return tk.tcl_call(tk.Color, 'tk_chooseColor', *_options(kwargs))


def _messagebox(type, title, message, detail=None, **kwargs):
    kwargs['type'] = type
    kwargs['title'] = title
    kwargs['message'] = message
    if detail is not None:
        kwargs['detail'] = detail

    if type == 'ok':
        tk.tcl_call(None, 'tk_messageBox', *_options(kwargs))
        return None
    if type == 'okcancel':
        return tk.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'ok'
    if type == 'retrycancel':
        return tk.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'retry'
    if type == 'yesno':
        return tk.tcl_call(str, 'tk_messageBox', *_options(kwargs)) == 'yes'

    # for anything else, return a string
    return tk.tcl_call(str, 'tk_messageBox', *_options(kwargs))


info = _partial(_messagebox, 'ok', icon='info')
warning = _partial(_messagebox, 'ok', icon='warning')
error = _partial(_messagebox, 'ok', icon='error')
ok_cancel = _partial(_messagebox, 'okcancel', icon='question')
retry_cancel = _partial(_messagebox, 'retrycancel', icon='warning')
yes_no = _partial(_messagebox, 'yesno', icon='question')
yes_no_cancel = _partial(_messagebox, 'yesnocancel', icon='question')
abort_retry_ignore = _partial(_messagebox, 'abortretryignore', icon='error')
