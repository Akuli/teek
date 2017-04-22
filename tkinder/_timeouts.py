import traceback

import tkinder
from tkinder import _mainloop


class Timeout:

    def __init__(self, after_what, callback, args, stack_info):
        self._callback = callback
        self._args = args
        callback_id = _mainloop.create_command(self._run, stack_info)
        self._id = tkinder.tk.call('after', after_what, callback_id)
        self._state = 'pending'   # just for __repr__ and error messages

    def __repr__(self):
        name = getattr(self._callback, '__name__', self._callback)
        return '<%s %r timeout at 0x%x>' % (self._state, name, id(self))

    def _run(self):
        try:
            self._callback(*self._args)
            self._state = 'successfully completed'
        except Exception as e:
            self._state = 'failed'
            raise e
        except BaseException as e:
            # this is probably intended so let's guess that it succeeded
            self._state = 'successfully completed'
            raise e

    def cancel(self):
        """Stop running this timeout."""
        if self._state != 'pending':
            raise RuntimeError("cannot cancel a %s timeout" % self._state)
        tkinder.tk.call('after', 'cancel', self._id)
        self._state = 'cancelled'


@_mainloop.requires_init
def after(milliseconds, callback, *args):
    """Run ``callback(*args)`` after waiting.

    This returns an object that has a ``cancel()`` method.
    """
    stack_info = traceback.format_stack()[-2]
    return Timeout(milliseconds, callback, args, stack_info)


@_mainloop.requires_init
def after_idle(callback, *args):
    """Run ``callback(*args)`` when no more tasks are pending.

    This returns an object that has a ``cancel()`` method.
    """
    # can't return after('idle', callback, *args) because this function
    # would show up in stack_info instead of whatever called this, same
    # thing with functools.partial
    stack_info = traceback.format_stack()[-2]
    return Timeout('idle', callback, args, stack_info)
