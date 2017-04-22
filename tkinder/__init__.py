# flake8: noqa

# this will be a _tkinter tkapp object, _mainloop.init() sets it but
# it's exposed here
tk = None

import sys as _sys

# tkinter's __init__.py does this
if _sys.platform.startswith("win32"):
    from tkinter import _fix

from tkinder._mainloop import init, mainloop, quit
from tkinder._timeouts import after, after_idle
from tkinder._widgets import Window, Label, Button
