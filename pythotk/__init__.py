# flake8: noqa

import os as _os
import sys as _sys

if _os.environ.get('READTHEDOCS', None) == 'True':   # pragma: no cover
    # readthedocs must be able to import everything without _tkinter
    import types
    _sys.modules['_tkinter'] = types.SimpleNamespace(
        TclError=None,
        TCL_VERSION='8.6',
        TK_VERSION='8.6',
    )
else:       # pragma: no cover
    # python 3.4's tkinter does this BEFORE importing _tkinter
    if _sys.platform.startswith("win32") and _sys.version_info < (3, 5):
        import tkinter._fix


# not to be confused with _tkinter's TclError, this is defined here because
# this way error messages say pythotk.TclError instead of
# pythotk._something.TclError, or worse yet, _tkinter.TclError
class TclError(Exception):
    """This is raised when a Tcl command fails."""


# _platform_info does a version check, it must be first
from pythotk._platform_info import TCL_VERSION, TK_VERSION, windowingsystem
from pythotk._font import Font, NamedFont
from pythotk._structures import (
    Callback, on_quit, Color, Image, ScreenDistance,
    TclVariable, StringVar, IntVar, FloatVar, BooleanVar)
from pythotk._tcl_calls import (
    tcl_call, tcl_eval, init_threads, create_command, delete_command,
    run, quit, update)
from pythotk._timeouts import after, after_idle
from pythotk._widgets.base import Widget
from pythotk._widgets.misc import (
    Button, Checkbutton, Entry, Frame, Label, LabelFrame, Separator)
from pythotk._widgets.notebook import Notebook, NotebookTab
from pythotk._widgets.text import Text
from pythotk._widgets.windows import Window, Toplevel
from pythotk import dialog
