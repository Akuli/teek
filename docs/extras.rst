Extras
======

.. module:: teek.extras

Big tkinter projects often have their own implementations of some commonly
needed things that tkinter doesn't come with. The ``teek.extras`` module
contains a collection of them.

To use the extras, ``import teek`` is not enough; that doesn't import
any extras. This is good because most teek programs don't need the extras,
and for them, ``import teek`` may run a little bit faster if it
doesn't import the extras. Instead, you typically need to do something like
this to use the extras::

    import teek
    from teek.extras import tooltips

    # now some code that uses tooltips.set_tooltip


.. module:: teek.extras.tooltips

tooltips
--------

This module contains a simple tooltip implementation with teek.
There is example code in :source:`examples/tooltip.py`.

If you have read some of IDLE's source code (if you haven't, that's
good; IDLE's source code is ugly), you might be wondering what this
thing has to do with ``idlelib/tooltip.py``. Don't worry, I didn't
copy/paste any code from idlelib and I didn't read idlelib while I
wrote the tooltip code! Idlelib is awful and I don't want to use
anything from it in my projects.

.. autofunction:: set_tooltip


.. module:: teek.extras.cross_platform

cross_platform
--------------

Most teek things work the same on most platforms, but not everything does.
For example, binding ``<Tab>`` works everywhere, but binding ``<Shift-Tab>``
doesn't work on Linux and you need a different binding instead. This extra
module contains utilities for dealing with things like that.

.. autofunction:: bind_tab_key


.. module:: teek.extras.more_dialogs

more_dialogs
------------

This is useful when :mod:`teek.dialog` is not enough.

All of the functions take these arguments:

* ``title`` will be the title of the dialog.
* ``text`` will be displayed in a label above the text entry or spinbox.
* ``initial_value`` will be added to the entry or spinbox before the user
  changes it.
* ``parent`` is a window widget that the dialog will be displayed on top of.

.. autofunction:: ask_string
.. autofunction:: ask_integer


.. module:: teek.extras.links

links
-----

With this extra, you can insert web browser style links to
:class:`~teek.Text` widgets. This is based on
`this tutorial <http://effbot.org/zone/tkinter-text-hyperlink.htm>`_ that is
almost as old as I am, but it's still usable.

See :source:`examples/links.py` for example code.

.. autofunction:: add_url_link
.. autofunction:: add_function_link


.. module:: teek.extras.image_loader

image_loader
------------

.. note::
    This extra has dependencies that don't come with teek when you install it
    with ``pip install teek`` or similar, because I want teek to be
    light-weight and I don't want to bring in lots of dependencies with it. Run
    ``pip install teek[image_loader]`` to install the things you need for using
    this extra.

    There's also ``image_loader_dummy``, which is like ``image_loader`` except
    that it just creates :meth:`teek.Image` objects, and doesn't support
    anything that plain :meth:`teek.Image` doesn't support. It's meant to be
    used like this::

        try:
            from teek.extras import image_loader
        except ImportError:
            from teek.extras import image_loader_dummy as image_loader

This extra lets you create :class:`teek.Image` objects of images that Tk itself
doesn't support. It uses other Python libraries like
`PIL <https://pillow.readthedocs.io/en/stable/>`_ and
`svglib <https://github.com/deeplook/svglib/>`_ to do that, and you can just
tell it to load an image and let it use whatever libraries are needed.

.. autofunction:: from_file
.. autofunction:: from_bytes
.. autofunction:: from_pil


.. module:: teek.extras.soup

soup
----

This extra contains code that views HTML to text widgets. The HTML is taken as
`BeautifulSoup <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_
elements, so you need to have it installed to use this module. Don't get too
excited though -- this is not something that's intended to be used for creating
a web browser or something, because this thing doesn't even support JavaScript
or CSS! It's meant to be used e.g. when you want to display some markup to the
user, and you know a library that can convert it to simple HTML.

If the HTML contains images that are not GIF images, make sure to install
:mod:`image_loader <teek.extras.image_loader>`. The ``soup`` extra will use it
if it's installed.

Only these HTML elements are supported by default (but you can subclass
:class:`SoupViewer` and add support for more elements, see
:meth:`SoupViewer.add_soup`):

* ``<h1>``, ``<h2>``, ``<h3>``, ``<h4>``, ``<h5>`` and ``<h6>``
* ``<pre>`` and ``<code>``
* ``<br>``
* ``<b>``, ``<i>``, ``<em>`` and ``<strong>``
* ``<p>``
* ``<ul>``, ``<ol>`` and ``<li>``
* ``<a>``
* ``<img>``

.. autoclass:: SoupViewer
    :members:
