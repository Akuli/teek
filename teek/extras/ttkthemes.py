import functools
import types

import teek

try:
    import ttkthemes as ttkthemes4tkinter
except ImportError:     # pragma: no cover
    ttkthemes4tkinter = None


# a future version of ttkthemes4tkinter might do something different than just
# the tkinter equivalent of this, so be sure to use its methods instead of this
# whenever needed
def _current_theme_directly_from_ttk():
    # this is commented in tkinter.ttk.Style.theme_use
    return teek.tcl_eval(str, 'return $ttk::currentTheme')


# welcome to my world of monkeypatching horror magic
# the good news is that rest of teek isn't like this at all

# ttkthemes4tkinter will use this class, so only put here stuff that
# ttkthemes4tkinter needs or may need in the future or whatever
class _FakeTkinterDotTtkDotStyle:

    def __init__(self):
        self.tk = types.SimpleNamespace(
            call=functools.partial(teek.tcl_call, [str]),
            eval=functools.partial(teek.tcl_eval, [str]),
        )

    def theme_use(self):
        return _current_theme_directly_from_ttk()


class ThemeManager:

    def __init__(self, *args, **kwargs):
        if ttkthemes4tkinter is None:
            self._style = None
        else:
            ttkthemes4tkinter.themed_style.ttk = types.SimpleNamespace(
                Style=_FakeTkinterDotTtkDotStyle)
            self._style = ttkthemes4tkinter.ThemedStyle(*args, **kwargs)

    def get_themes(self):
        if self._style is None:
            return teek.tcl_call([str], 'ttk::themes')
        return self._style.get_themes()

    @property
    def current_theme(self):
        if self._style is None:
            return _current_theme_directly_from_ttk()
        return self._style.theme_use()

    @current_theme.setter
    def current_theme(self, new_theme):
        if self._style is None:
            # this is commented in tkinter.ttk.Style.theme_use
            teek.tcl_call(None, 'ttk::setTheme', new_theme)
        else:
            self._style.set_theme(new_theme)
