.. _eventloop:

Event Loop
==========

Tk is event-based. When you click a :class:`~teek.Button`, a click event is
generated, and Tk processes it. Usually that involves making the button look
like it's pressed down, and maybe calling a callback function that you have
told the button to run.

The **event loop** works essentially like this pseudo code::

    while True:
        handle_an_event()
        if there_are_no_more_events_because_we_handled_all_of_them:
            wait_for_more_events()

These functions can be used for working with the event loop:

.. autofunction:: teek.run
.. autofunction:: teek.quit

.. data:: teek.before_quit

    :func:`.quit` runs this callback with no arguments before it does anything
    else. This means that when this callback runs, widgets have not been
    destroyed yet, but they will be destroyed soon.

.. data:: teek.after_quit

    :func:`.quit` runs this callback when it has done everything else
    successfully.

.. autofunction:: teek.update
