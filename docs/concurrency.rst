.. _concurrency:

Concurrency
===========

This page is all about running things concurrently in teek. That means doing
something else while the GUI is running.


.. _threads:

Threads
-------

Here is some code that pastebins a Hello World to
`dpaste.com <http://dpaste.com/>`_.
::

    import requests
    import teek


    class Dpaster(teek.Frame):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.paste_button = teek.Button(self, "Pastebin a hello world", self.paste)
            self.paste_button.pack()

            self.url_label = teek.Label(self)
            self.url_label.pack()

        def paste(self):
            self.url_label.config['text'] = "Pasting..."

            # api docs: http://dpaste.com/api/v2/
            print("Starting to paste")
            response = requests.post('http://dpaste.com/api/v2/',
                                     data={'content': 'Hello World'})
            response.raise_for_status()
            url = response.text.strip()
            print("Pasted successfully:", url)

            self.url_label.config['text'] = url


    window = teek.Window("dpaster")
    Dpaster(window).pack()
    window.geometry(250, 100)
    window.on_delete_window.connect(teek.quit)
    teek.run()

Run the program. If you click the pasting button, the whole GUI freezes for a
couple seconds and the button looks like it's pressed down, and when the
pastebinning is done, everything is fine again. **The freezing is not nice.**

In this documentation, functions and methods that take a long time to complete
are called **blocking**. Our ``paste()`` method is blocking, and using a
blocking function or method as a button click callback freezes things.

If you have code like this...
::

    import time


    def one_thing():
        print("one thing")
        time.sleep(1)
        print("one thing")
        time.sleep(1)
        print("one thing")


    def another_thing():
        print("another thing")
        time.sleep(1)
        print("another thing")
        time.sleep(1)
        print("another thing")


    one_thing()
    another_thing()

...Python obviously doesn't run ``one_thing()`` and ``another_thing()`` at the
same time; it'll first run ``one_thing()``, and when it's done, it'll run
``another_thing()``. However, if we add ``import threading`` to the top of the
program and change the last 2 lines to this...
::

    threading.Thread(target=one_thing).start()
    another_thing()

...the functions *will* run at the same time.

.. note::
    We are doing ``target=one_thing``, **not** ``target=one_thing()``. The
    ``()`` at the end of ``one_thing()`` tell Python to run the function right
    away, but instead of that, we want to run it in the thread.

The good *\*ehm\** **awesome** news is that threads work nicely in teek.
Add ``import threading`` to the top of the file, and add this method to the
``Dpaster`` class...
::

    def start_pasting(self):
        threading.Thread(target=self.paste).start()

...and change the line that creates ``self.paste_button`` to this::

    self.paste_button = teek.Button(self, "Pastebin a hello world", self.start_pasting)

Let's try to run the program again. Clicking the button gives this error:

.. code-block:: py3tb

    Traceback (most recent call last):
        ...
    RuntimeError: init_threads() wasn't called

Let's fix it by adding ``teek.init_threads()`` before the line that creates
``window``. All in all, the code looks like this now::

    import threading

    import requests
    import teek


    class Dpaster(teek.Frame):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.paste_button = teek.Button(self, "Pastebin a hello world", self.start_pasting)
            self.paste_button.pack()

            self.url_label = teek.Label(self)
            self.url_label.pack()

        def start_pasting(self):
            threading.Thread(target=self.paste).start()

        def paste(self):
            self.url_label.config['text'] = "Pasting..."

            # api docs: http://dpaste.com/api/v2/
            print("Starting to paste")
            response = requests.post('http://dpaste.com/api/v2/',
                                     data={'content': 'Hello World'})
            response.raise_for_status()
            url = response.text.strip()
            print("Pasted successfully:", url)

            self.url_label.config['text'] = url


    teek.init_threads()
    window = teek.Window("dpaster")
    Dpaster(window).pack()
    window.geometry(250, 100)
    window.on_delete_window.connect(teek.quit)
    teek.run()

Run the program. It works!


How does it work, and why did it freeze??
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    This section assumes that you know :ref:`event loop stuff <eventloop>`.

Button click callbacks are ran in the event loop. If the button command takes
2 seconds or so to run, the event loop will run it for 2 seconds, but it can't
do anything else while it's doing that (see the event loop stuff link above to
understand why). However, ``start_pasting()`` is not blocking, and running that
from the event loop is fine.

If you have used ``tkinter`` before, the above program probably looks quite
wrong to you, because in tkinter, running anything like
``self.url_label.config['text'] = "Pasting..."`` in a thread is **BAD**.
Threads and tkinter don't work together well, and you must not do *any* tkinter
stuff from threads. If you wanted to write the pastebinning program in tkinter,
you would need to do quite a few things yourself:

* Create a :class:`~queue.Queue` that will contain texts of ``self.url_label``.
  Queues can be used from threads **and** from Tk's event loop, so we can use
  them to communicate between the pastebinning thread and the event loop.
* Create a method that gets a text from the queue and sets it to
  ``self.url_label``.

    * This method needs to use the tkinter label, so it must not be called from
      a thread because tkinter and threads don't mix well. The only other way
      to call it is from tkinter's event loop.
    * Because the method is called from tkinter's event loop, it must not
      block; that is, it can't wait until a message arrives to the queue from
      the thread. If there are no messages in the queue, it must do nothing.
    * Because the method can't wait for messages in the thread, and it can only
      check if there are messages, it must be ran repeatedly e.g. 20 times per
      second. The thread will then add a message to the queue, and the queue
      clearing method will do something with that message soon.
    * Because the method must be called 20 times per second, you must tell the
      event loop to run it 20 times per second. The only way to do this is with
      :ref:`after callbacks <after-cb>`.

If you accidentally call a tkinter thing from a thread, you may get very weird
behaviour (but in teek, you get a :exc:`RuntimeError` as shown above):

* Things may work 90% of the time and break 10% of the time.
* Everything may work just fine on your computer but not on someone else's
  computer.
* When things break, you get confusing error messages that don't necessarily
  say anything about threads.

Furthermore, beginners often want to use threads with tkinter, and they
struggle with it a lot, which is no surprise. Threading with tkinter is hard.

Teek's ``init_threads()`` does the hard things for you:

.. autofunction:: teek.init_threads

If you use ``init_threads()``, you can also use this decorator:

.. autofunction:: teek.make_thread_safe


Letting the user know that something is happening
-------------------------------------------------

Here is a part of our example program above.
::

    def __init__(self, *args, **kwargs):
        ...
        self.paste_button = teek.Button(self, "Pastebin a hello world", self.start_pasting)
        ...

    def start_pasting(self):
        threading.Thread(target=self.paste).start()

    def paste(self):
        self.url_label.config['text'] = "Pasting..."
        ...
        self.url_label.config['text'] = url

Can you see the problem? The paste button can be clicked while ``paste()`` is
running in the thread. If the user does that, we have two pastes running at the
same time in different threads. That's not nice.

A simple alternative is to make the button grayed out in the paste function::

    def paste(self):
        self.paste_button.state.add('disabled')
        self.url_label.config['text'] = "Pasting..."
        ...
        self.url_label.config['text'] = url
        self.paste_button.state.remove('disabled')

See :attr:`.Widget.state` for documentation about the state thing.

If you don't want to disable widgets or you would need to disable a widget and
all widgets in it, you can use :meth:`.Widget.busy` instead, like this::

    def paste(self):
        with self.busy():
            self.url_label.config['text'] = "Pasting..."
            ...
            self.url_label.config['text'] = url

Here is the reference.

.. automethod:: teek.Widget.busy_hold
.. automethod:: teek.Widget.busy_forget
.. automethod:: teek.Widget.busy_status
.. automethod:: teek.Widget.busy

For more advanced things, you can also use a separate :class:`.Progressbar`
widget.


.. _after-cb:

After Callbacks
---------------

Sometimes :ref:`threads <threads>` are overkill. Here is a clock program::

    import threading
    import time

    import teek


    class Clock(teek.Frame):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.label = teek.Label(self)
            self.label.pack()

            threading.Thread(target=self.updater_thread).start()

        def updater_thread(self):
            while True:
                self.label.config['text'] = time.asctime()
                time.sleep(1)


    teek.init_threads()
    window = teek.Window("Clock")
    Clock(window).pack()
    window.on_delete_window.connect(teek.quit)
    teek.run()

.. admonition:: BTW

    If you close the window that the above program creates, you get a
    :exc:`RuntimeError` saying that :func:`.init_threads` wasn't called,
    because closing the window calls :func:`.quit` and :func:`.init_threads`
    would need to be called again after a :func:`.quit`. You can make the
    program exit cleanly by replacing this...
    ::

        self.label.config['text'] = time.asctime()

    ...with this::

        try:
            self.label.config['text'] = time.asctime()
        except RuntimeError:
            # the program is quitting
            return

    Returning from the thread target will stop the thread, and Python will exit
    because no more threads are running.

The repeatedly called ``time.sleep(1)`` in ``updater_thread()`` tells you that
after callbacks might be a better alternative. They work like this::

    import time

    import teek


    class Clock(teek.Frame):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.label = teek.Label(self)
            self.label.pack()
            self.updater_callback()

        def updater_callback(self):
            self.label.config['text'] = time.asctime()

            # tell tk to run this again after 1 second
            teek.after(1000, self.updater_callback)


    window = teek.Window("Clock")
    Clock(window).pack()
    window.on_delete_window.connect(teek.quit)
    teek.run()

``teek.after(1000, self.updater_callback)`` runs ``self.updater_callback()`` in
Tk's event loop after 1000 milliseconds; that is, 1 second.

.. autofunction:: teek.after
.. autofunction:: teek.after_idle

See also :man:`after(3tcl)`.

It's also possible to cancel a timeout before it runs. :func:`.after` and
:func:`.after_idle` return **timeout objects**, which have a method for
canceling:

.. method:: timeout_object.cancel()

    Prevent this timeout from running as scheduled.

    :exc:`RuntimeError` is raised if the timeout has already ran or it has been
    cancelled.

Timeout objects also have a useful string representation for debugging:

>>> teek.after(1000, print)       # doctest: +ELLIPSIS
<pending 'print' timeout 'after#...'>
