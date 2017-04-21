# flake8: noqa

import sys as _sys

# tkinter's __init__.py does this
if _sys.platform.startswith("win32"):
    from tkinter import _fix

from ._mainloop import init, mainloop, quit
from ._widgets import Window, Label
