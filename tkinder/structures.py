import keyword
import sys
import traceback
import _tkinter

import tkinder
from tkinder import _utils


class Callback:
    """An object that calls multiple functions.

    >>> c = Callback()
    >>> c.connect(print, "hello")
    >>> c.connect(print, "hello", "again")
    >>> c.run("world")      # usually tkinder does this
    hello world
    hello again world
    """

    def __init__(self):
        self._connections = []

    def connect(self, function, *extra_args):
        # -1 is this method so -2 is what called this
        stack_info = traceback.format_stack()[-2]
        self._connections.append((function, extra_args, stack_info))

    def disconnect(self, function):
        for index, infotuple in enumerate(self._connections):
            # can't use is because python makes up method objects dynamically:
            #   >>> class Thing:
            #   ...   def stuff(): pass
            #   ...
            #   >>> t = Thing()
            #   >>> t.stuff is t.stuff
            #   False
            #   >>> t.stuff == t.stuff
            #   True
            if infotuple[0] == function:
                del self._connections[index]
                return
        raise ValueError("not connected: %r" % (function,))

    def run(self, *args):
        for func, extra_args, stack_info in self._connections:
            try:
                func(*(extra_args + args))
            except SystemExit as e:
                # this doesn't actually exit python, but it's a handy
                # way to end the main loop :)
                if not (isinstance(e.code, int) or e.code is None):
                    print(e.code, file=sys.stderr)
                tkinder.quit()
                break
            except Exception:
                _utils.print_callback_traceback(stack_info)
                break


class _Config:
    """A view of a widget's options.

    The options can be used like attributes:
        some_label.config.text = "Hello World!"
        print(some_label.config.text)

    Or with a tkinter-style method call:
        some_label.config(text="Hello World!")

    It's also possible to iterate over the options:
        for option, value in some_label.config:
            print(option, value)

    Or you can convert the options to a dictionary:
        the_options = dict(some_label.config)
    """

    def __init__(self, widget):
        self._widget = widget
        self._special_options = {}

    def _set(self, option, value):
        if option in self._special_options:
            setter, getter = self._special_options[option]
            setter(value)
        else:
            tkinder.tk.call(self._widget.path, 'config', '-' + option, value)

    def _get(self, option):
        if option in self._special_options:
            setter, getter = self._special_options[option]
            return getter()
        return tkinder.tk.call(self._widget.path, 'cget', '-' + option)

    def __setattr__(self, option, value):
        if option.startswith('_'):
            # it's an attribute from this class, __magic__ or something else
            super().__setattr__(option, value)
            return

        try:
            # the rstrip supports options like from_
            self._set(option.rstrip('_'), value)
        except _tkinter.TclError as error:
            raise AttributeError(str(error)) from None

    def __getattr__(self, option):
        try:
            return self._get(option.rstrip('_'))
        except _tkinter.TclError as error:
            raise AttributeError(str(error)) from None

    # dict() uses this
    def __iter__(self):
        options = set(self._special_options.keys())
        for option, *junk in tkinder.tk.call(self._widget.path, 'config'):
            options.add(option.lstrip('-'))

        for option in sorted(options):
            try:
                yield option, self._get(option)
            except _tkinter.TclError:
                # the option isn't available
                pass

    def __dir__(self):
        result = []
        for option, value in self:
            if keyword.iskeyword(option):
                # this appends _ because dir() is used for autocompleting
                option += '_'
            result.append(option)

        result.sort()
        return result

    def __call__(self, **kwargs):
        if not kwargs:
            # tkinter treats this case specially and it can be confusing
            raise TypeError("config() requires arguments")
        for option, value in kwargs.items():
            self._set(option, value)


if __name__ == '__main__':
    import doctest
    print(doctest.testmod())
