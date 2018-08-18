# flake8: noqa

import os as _os
import sys as _sys

if _sys.platform.startswith("win32"):     # pragma: no cover
    try:
        # tkinter's __init__.py does this with some python versions, i haven't
        # checked which
        from tkinter import _fix
    except ImportError:
        pass

if _os.environ.get('READTHEDOCS', None) == 'True':   # pragma: no cover
    # readthedocs must be able to import everything without _tkinter
    import types
    _sys.modules['_tkinter'] = types.SimpleNamespace(
        TclError=None,
    )

from _tkinter import TclError
from pythotk._structures import Callback, Color
from pythotk._tcl_calls import (
    call, eval, create_command, delete_command, run, quit, on_quit)
from pythotk._timeouts import after, after_idle
from pythotk._misc import update      # TODO: move this to _timeouts?

# simplest widgets are in pythotk._widgets, but widgets that require many lines
# of code to implement are in separate files
from pythotk._widgets import (
    Widget, Window, Toplevel, Label, Button, Frame, Separator)
from pythotk._textwidget import Text
