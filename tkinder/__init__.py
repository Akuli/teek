# flake8: noqa

import sys as _sys

# tkinter's __init__.py does this
if _sys.platform.startswith("win32"):     # pragma: no cover
    from tkinter import _fix

from _tkinter import TclError
from tkinder._structures import Callback
from tkinder._mainloop import (
    call, eval, create_command, delete_command, run, quit, on_quit)
from tkinder._timeouts import after, after_idle
from tkinder._misc import update      # TODO: move this to _timeouts?
from tkinder._widgets import Widget, Window, Toplevel, Label, Button, Frame
