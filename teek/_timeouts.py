import teek
from teek._tcl_calls import make_thread_safe


# there's no after_info because i don't see how it would be useful in
# teek

class _Timeout:

    def __init__(self, after_what, callback, args, kwargs):
        if kwargs is None:
            kwargs = {}

        self._callback = callback
        self._args = args
        self._kwargs = kwargs

        self._state = 'pending'   # just for __repr__ and error messages
        self._tcl_command = teek.create_command(self._run)
        self._id = teek.tcl_call(str, 'after', after_what, self._tcl_command)

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

        teek.before_quit.connect(quit_callback)

        try:
            self._callback(*self._args, **self._kwargs)
            self._state = 'successfully completed'
        except Exception as e:
            self._state = 'failed'
            raise e
        finally:
            teek.before_quit.disconnect(quit_callback)
            if needs_cleanup:
                teek.delete_command(self._tcl_command)

    @make_thread_safe
    def cancel(self):
        """Prevent this timeout from running as scheduled.

        :exc:`RuntimeError` is raised if the timeout has already ran or
        it has been cancelled.

        There is example code in :source:`examples/timeout.py`.
        """
        if self._state != 'pending':
            raise RuntimeError("cannot cancel a %s timeout" % self._state)
        teek.tcl_call(None, 'after', 'cancel', self._id)
        self._state = 'cancelled'
        teek.delete_command(self._tcl_command)


@make_thread_safe
def after(ms, callback, args=(), kwargs=None):
    """Run ``callback(*args, **kwargs)`` after waiting for the given time.

    The *ms* argument should be a waiting time in milliseconds, and
    *kwargs* defaults to ``{}``. This returns a timeout object with a
    ``cancel()`` method that takes no arguments; you can use that to
    cancel the timeout before it runs.
    """
    return _Timeout(ms, callback, args, kwargs)


@make_thread_safe
def after_idle(callback, args=(), kwargs=None):
    """Like :func:`after`, but runs the timeout as soon as possible."""
    return _Timeout('idle', callback, args, kwargs)
