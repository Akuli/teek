.. _menu:

Menu Widget
===========

**Manual page:** :man:`menu(3tk)`

You can use menu widges for a few different things:

* **Menu bars** are menus that are typically displayed at the top of a window,
  or top of the screen if you are using e.g. Mac OSX.
* **Pop-up menus** open when the user e.g. right-clicks something.

Here is an example of a menu bar::

    import teek as tk

    window = tk.Window()

    def hello():
        print("hello")

    window.config['menu'] = tk.Menu([
        tk.MenuItem("File", [
            tk.MenuItem("New", hello),
            tk.MenuItem("Open", hello),
            tk.MenuItem("Save", hello),
            tk.MenuItem("Quit", hello),
        ]),
        tk.MenuItem("Edit", [
            tk.MenuItem("Cut", hello),
            tk.MenuItem("Copy", hello),
            tk.MenuItem("Paste", hello),
        ]),
    ])

    window.geometry(300, 200)
    window.on_delete_window.connect(tk.quit)
    tk.run()

As you can see, :class:`.Menu` takes one argument, which is a list of
:class:`.MenuItem` objects. This example uses two kinds of menu items; some
menu items just call the ``hello()`` function when they are clicked, while the
"File" and "Edit" items display submenus. There are more details about
different kinds of items :ref:`below <creating-menu-items>`.

Here is a pop-up menu example. See :ref:`bind documentation <binding>` for more
details about the binding stuff.
::

    import teek as tk

    window = tk.Window()

    def hello():
        print("hello")

    menu = tk.Menu([
        tk.MenuItem("Cut", hello),
        tk.MenuItem("Copy", hello),
        tk.MenuItem("Paste", hello),
    ])

    def on_right_click(event):
        menu.popup(event.rootx, event.rooty)

    if tk.windowingsystem() == 'aqua':
        # running on Mac OSX, there's no right-click so this must be done a bit
        # differently
        window.bind('<Button-2>', on_right_click, event=True)
        window.bind('<Control-Button-1>', on_right_click, event=True)
    else:
        window.bind('<Button-3>', on_right_click, event=True)

    window.geometry(300, 200)
    window.on_delete_window.connect(tk.quit)
    tk.run()

I found the Mac OSX specific code from here_.

.. _here: https://books.google.fi/books?id=BWf6mdwHjDMC&pg=PT392&lpg=PT392&dq=tk_popup+vs+post&source=bl&ots=n32EYTF27b&sig=V0xXtCqHmKKa37BRNCdPk6unhr4&hl=fi&sa=X&ved=2ahUKEwikwa7A0pzdAhVKCCwKHSeNCa4Q6AEwBHoECAYQAQ#v=onepage&q=tk_popup%20vs%20post&f=false

Menu widgets are *not* Ttk widgets. If you don't know what that means, you
should go :ref:`here <tcl-tk-tkinter-teek>` and learn. The only practical
thing I can think of right now is that menus don't have a
:attr:`~.Widget.state` attribute.


.. _creating-menu-items:

Creating Menu Items
~~~~~~~~~~~~~~~~~~~

There are a few different ways to create instances of :class:`.MenuItem`. Here
``label`` must be a string.

.. TODO: create a Radiobutton widget

* ``MenuItem()`` creates a separator.
* ``MenuItem(label, function)`` creates a ``command`` item that runs
  ``function()`` when it's clicked. See also :class:`.Button`.
* ``MenuItem(label, checked_var)`` creates a ``checkbutton`` menu item. The
  ``checked_var`` must be a :class:`.BooleanVar`. See also
  :class:`.Checkbutton`.
* ``MenuItem(label, string_var, value)`` creates a ``radiobutton`` menu item.
  Use this for letting the user choose one of multiple options. Clicking the
  item sets ``value`` to ``string_var``. The ``string_var`` must be a
  :class:`.StringVar` object, and ``value`` must be a string.
* ``MenuItem(label, menu)`` creates a ``cascade`` menu item; that is, it
  displays a submenu with the items of ``menu`` in it. The ``menu`` must be a
  :class:`.Menu` widget.
* ``MenuItem(label, item_list)`` is a handy way to create a new :class:`.Menu`
  and add it as a ``cascade`` item as explained above.

You can also pass options as keyword arguments in any of the above forms. The
available options are documented as ``MENU ENTRY OPTIONS`` in :man:`menu(3tk)`.
For example, instead of this...
::

    MenuItem("Copy", do_the_copy)

...you probably want to do something like this::

    MenuItem("Copy", do_the_copy, accelerator='Ctrl+C')

Note that this does not :ref:`bind <binding>` anything automatically, so you
need to do that yourself if want that Ctrl+C actually does something.

Here is an example that demonstrates most things. See :class:`.StringVar` and
:class:`.BooleanVar` documentation for more info about them.
::

    import teek as tk


    def on_click():
        print("clicked")

    def on_check(is_checked):
        print("is it checked now?", is_checked)

    def on_choice(choice):
        print("chose", repr(choice))


    window = tk.Window()

    submenu = tk.Menu([
        tk.MenuItem("Asd", on_click),
        tk.MenuItem("Toot", on_click),
    ])

    check_var = tk.BooleanVar()
    check_var.write_trace.connect(on_check)
    choice_var = tk.StringVar()
    choice_var.write_trace.connect(on_choice)

    window.config['menu'] = tk.Menu([
        tk.MenuItem("Stuff", [
            tk.MenuItem("Click me", on_click),
            tk.MenuItem("Check me", check_var),
            tk.MenuItem("More stuff", submenu),
            tk.MenuItem(),      # separator
            tk.MenuItem("Choice 1", choice_var, "one"),
            tk.MenuItem("Choice 2", choice_var, "two"),
            tk.MenuItem("Choice 3", choice_var, "three"),
        ]),
    ])

    window.geometry(300, 200)
    window.on_delete_window.connect(tk.quit)
    tk.run()


Reference
~~~~~~~~~

.. explicit member list for same reason as with Notebook

.. autoclass:: teek.Menu
    :members: popup

.. autoclass:: teek.MenuItem
    :members:
