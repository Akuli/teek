import pythotk as tk


class _TooltipManager:

    # This needs to be shared by all instances because there's only one
    # mouse pointer.
    tipwindow = None

    def __init__(self, widget: tk.Widget):
        widget.bind('<Enter>', self.enter, event=True)
        widget.bind('<Leave>', self.leave, event=True)
        widget.bind('<Motion>', self.motion, event=True)
        self.widget = widget
        self.got_mouse = False
        self.text = None

    @classmethod
    def destroy_tipwindow(cls):
        if cls.tipwindow is not None:
            cls.tipwindow.destroy()
            cls.tipwindow = None

    def enter(self, event):
        # For some reason, toplevels get also notified of their
        # childrens' events.
        if event.widget is self.widget:
            self.destroy_tipwindow()
            self.got_mouse = True
            tk.after(1000, self.show)

    def leave(self, event):
        if event.widget is self.widget:
            self.destroy_tipwindow()
            self.got_mouse = False

    def motion(self, event):
        self.mousex = event.rootx
        self.mousey = event.rooty

    def show(self):
        if not self.got_mouse:
            return

        self.destroy_tipwindow()
        if self.text is not None:
            # the label and the tipwindow are not ttk widgets because that way
            # they can look different than other widgets, which is what
            # tooltips are usually like
            tipwindow = type(self).tipwindow = tk.Toplevel()
            tipwindow.geometry(x=(self.mousex + 10), y=(self.mousey - 10))
            tipwindow.bind('<Motion>', self.destroy_tipwindow)

            # TODO: add overrideredirect to pythotk
            tk.tcl_call(None, 'wm', 'overrideredirect', tipwindow, 1)

            # i don't think there's a need to add better support for things
            # like non-ttk labels because they are not needed very often
            #
            # refactoring note: if you change this, make sure that either BOTH
            # of fg and bg are set, or NEITHER is set, because e.g. bg='white'
            # with no fg gives white text on white background on systems with
            # white default foreground, but works fine on systems with black
            # default foreground
            label = tk.tcl_call(str, 'label', tipwindow.to_tcl() + '.label',
                                '-text', self.text, '-border', 3,
                                '-fg', 'black', '-bg', '#ffc')
            tk.tcl_call(None, 'pack', label)


def set_tooltip(widget, text):
    """A simple tooltip implementation with pythotk.

    After calling ``set_tooltip(some_widget, "hello")``, "hello" will be
    displayed in a small window when the user moves the mouse over the
    widget and waits for a small period of time. Do
    ``set_tooltip(some_widget, None)`` to get rid of a tooltip.

    If you have read some of IDLE's source code (if you haven't, that's
    good; IDLE's source code is ugly), you might be wondering what this
    thing has to do with ``idlelib/tooltip.py``. Don't worry, I didn't
    copy/paste any code from idlelib and I didn't read idlelib while I
    wrote the tooltip code! Idlelib is awful and I don't want to use
    anything from it in my projects.
    """
    if text is None:
        if hasattr(widget, '_tooltip_manager'):
            widget._tooltip_manager.text = None
    else:
        if not hasattr(widget, '_tooltip_manager'):
            widget._tooltip_manager = _TooltipManager(widget)
        widget._tooltip_manager.text = text
