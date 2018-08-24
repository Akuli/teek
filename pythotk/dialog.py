from pythotk._tcl_calls import tcl_call
from pythotk._structures import Color


def color(**kwargs):
    """Calls :man:`tk_chooseColor(3tk)`.

    The color selected by the user is returned, or ``None`` if the user
    cancelled the dialog.
    """
    options = []
    for name, value in kwargs.items():
        options.extend(['-' + name, value])

    return tcl_call(Color, 'tk_chooseColor', *options)
