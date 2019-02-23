import teek


class _EntryDialog:

    def __init__(self, title, text, entry_creator, validator,
                 initial_value, parent):
        self.validator = validator

        self.window = teek.Window(title)
        self.window.on_delete_window.connect(self.on_cancel)
        if parent is not None:
            self.window.transient = parent

        self.var = teek.StringVar()

        teek.Label(self.window, text).grid(row=0, column=0, columnspan=2)
        entry = entry_creator(self.window)
        entry.config['textvariable'] = self.var
        entry.grid(row=1, column=0, columnspan=2)
        entry.bind('<Return>', self.on_ok)
        entry.bind('<Escape>', self.on_cancel)

        self.ok_button = teek.Button(self.window, "OK", self.on_ok)
        self.ok_button.grid(row=3, column=0)
        teek.Button(self.window, "Cancel", self.on_cancel).grid(
            row=3, column=1)

        self.window.grid_rows[0].config['weight'] = 1
        self.window.grid_rows[2].config['weight'] = 1
        for column in self.window.grid_columns:
            column.config['weight'] = 1

        self.result = None
        self.var.write_trace.connect(self.on_var_changed)
        self.var.set(initial_value)
        self.on_var_changed(self.var)   # TODO: is this needed?

        # TODO: add a way to select stuff to teek
        self.window.geometry(300, 150)
        entry.focus()
        teek.tcl_call(None, entry, 'selection', 'range', '0', 'end')

    def on_var_changed(self, var):
        result = self.var.get()
        try:
            self.result = self.validator(result)
            self.ok_button.config['state'] = 'normal'
        except ValueError:
            self.result = None
            self.ok_button.config['state'] = 'disabled'

    def on_ok(self):
        # this state check is needed because <Return> is bound to this, and
        # that binding can run even if the button is disabled
        if self.ok_button.config['state'] == 'normal':
            self.window.destroy()

    def on_cancel(self):
        self.result = None
        self.window.destroy()

    def run(self):
        self.window.wait_window()
        return self.result


def ask_string(title, text, *, validator=str, initial_value='', parent=None):
    """Displays a dialog that contains a :class:`teek.Entry` widget.

    The ``validator`` should be a function that takes a string as an argument,
    and returns something useful (see below). By default, it returns the string
    unchanged, which is useful for asking a string from the user. If the
    validator raises :exc:`ValueError`, the OK button of the dialog is disabled
    to tell the user that the value they entered is invalid. Then the user
    needs to enter a valid value or cancel the dialog.

    This returns whatever ``validator`` returned, or ``None`` if the dialog was
    canceled.
    """
    return _EntryDialog(title, text, teek.Entry, validator, initial_value,
                        parent).run()


def ask_integer(title, text, allowed_values, *, initial_value=None,
                parent=None):
    """Displays a dialog that contains a :class:`teek.Spinbox` widget.

    ``allowed_values`` can be a sequence of acceptable integers or a
    :class:`range`. If ``initial_value`` is given, it must be in
    ``allowed_values``. If it's not, ``allowed_values[0]`` is used.

    This returns an integer in ``allowed_values``, or ``None`` if the user
    cancels.
    """
    def creator(spinbox_parent):
        if isinstance(allowed_values, range):
            # range(blah, blah, 0) raises an error, so the step can't be zero
            if allowed_values.step < 0:
                raise ValueError(
                    "ranges with negative steps are not supported")

            # allowed_values.stop is not same as allowed_values[-1], the -1 one
            # is inclusive
            return teek.Spinbox(
                spinbox_parent, from_=allowed_values[0], to=allowed_values[-1],
                increment=allowed_values.step)

        return teek.Spinbox(spinbox_parent, values=allowed_values)

    def validator(value):
        int_value = int(value)
        if int_value not in allowed_values:
            raise ValueError
        return int_value

    if initial_value is None:
        initial_value = allowed_values[0]
    elif initial_value not in allowed_values:
        raise ValueError("initial value %r not in %r"
                         % (initial_value, allowed_values))

    return _EntryDialog(title, text, creator, validator, initial_value,
                        parent).run()
