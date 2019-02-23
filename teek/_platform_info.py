import _tkinter

import teek


# i'm not sure if these can be different, but why not allow that i guess... lol
TCL_VERSION = tuple(map(int, _tkinter.TCL_VERSION.split('.')))
TK_VERSION = tuple(map(int, _tkinter.TK_VERSION.split('.')))


# this is a function to make this testable
def _version_check():
    if TK_VERSION < (8, 5) or TCL_VERSION < (8, 5):
        raise RuntimeError(
            "sorry, your Tcl/Tk installation is too old "
            "(expected 8.5 or newer, found Tcl %d.%d and Tk %d.%d)"
            % (TCL_VERSION + TK_VERSION))


_version_check()


def windowingsystem():
    return teek.tcl_call(str, 'tk', 'windowingsystem')
