.. _getting-started:

Getting Started with Pythotk
============================

This page shows you some basic things you need to know when programming with
pythotk.


.. _eventloop:

Event Loop
----------

Tk is event-based. When you click a :class:`~pythotk.Button`, a click event is
generated, and Tk processes it. Usually that involves making the button look
like it's pressed down, and maybe calling a callback function that you have
told the button to run.

The **event loop** works essentially like this pseudo code::

    while True:
        handle_an_event()
        if there_are_no_more_events_because_we_handled_all_of_them:
            wait_for_more_events()

.. autofunction:: pythotk.run
.. autofunction:: pythotk.quit
