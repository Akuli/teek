import traceback

from pythotk import TclError
from pythotk._tcl_calls import call, on_quit, create_command, delete_command

# there's no after_info because i don't see how it would be useful in
# pythotk


class _Timeout:

    def __init__(self, after_what, callback, args, kwargs, stack_info):
        if kwargs is None:
            kwargs = {}

        self._callback = callback
        self._args = args
        self._kwargs = kwargs

        self._state = 'pending'   # just for __repr__ and error messages
        self._tcl_command = create_command(self._run, stack_info=stack_info)
        self._id = call(str, 'after', after_what, self._tcl_command)

    def __repr__(self):
        name = getattr(self._callback, '__name__', self._callback)
        return '<%s %r timeout %r>' % (self._state, name, self._id)

    def _run(self):
        needs_cleanup = True

        # this is important, thread tests freeze without this special
        # case for some reason
        def quit_callback():
            nonlocal needs_cleanup
            needs_cleanup = False

        on_quit.connect(quit_callback)

        try:
            self._callback(*self._args, **self._kwargs)
            self._state = 'successfully completed'
        except Exception as e:
            self._state = 'failed'
            raise e
        finally:
            on_quit.disconnect(quit_callback)
            if needs_cleanup:
                delete_command(self._tcl_command)

    def cancel(self):
        """Prevent this timeout from running as scheduled.

        :exc:`RuntimeError` is raised if the timeout has already ran or
        it has been cancelled.
        """
        if self._state != 'pending':
            raise RuntimeError("cannot cancel a %s timeout" % self._state)
        call(None, 'after', 'cancel', self._id)
        self._state = 'cancelled'
        delete_command(self._tcl_command)


def after(ms, callback, args=(), kwargs=None):
    """Run ``callback(*args, **kwargs)`` after waiting for the given time.

    The *ms* argument should be a waiting time in milliseconds, and
    *kwargs* defaults to ``{}``. This returns a timeout object with a
    ``cancel()`` method that takes no arguments; you can use that to
    cancel the timeout before it runs.
    """
    stack_info = traceback.format_stack()[-2]
    return _Timeout(ms, callback, args, kwargs, stack_info)


def after_idle(callback, args=(), kwargs=None):
    """Like :func:`after`, but runs the timeout as soon as possible."""
    stack_info = traceback.format_stack()[-2]
    return _Timeout('idle', callback, args, kwargs, stack_info)
