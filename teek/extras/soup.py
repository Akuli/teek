import contextlib
import functools
import itertools
import re
import threading
import urllib.request
import warnings

import teek
from teek.extras import links
try:
    from teek.extras import image_loader
except ImportError:
    from teek.extras import image_loader_dummy as image_loader


class SoupViewer:
    """Displays BeautifulSoup_ HTML elements in a text widget.

    .. BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/

    .. note::
        If the soup contains ``<img>`` tags, the images are read or downloaded
        automatically by default. Subclass :class:`SoupViewer` and override
        :meth:`download` if you don't want that.

        Images are loaded in threads, so make sure to use
        :func:`teek.init_threads`. Alternatively, you can pass
        ``threads=False``, and the images won't be loaded at all.

    .. attribute:: widget

        The :class:`teek.Text` widget that everything is added to.
    """

    def __init__(self, textwidget, threads=True):
        self._use_threads = threads
        self.widget = textwidget
        self.widget.bind('<Destroy>',
                         functools.partial(self.stop_loading, cleanup=True))
        self._image_mark_names = ('soup-img-' + str(i)
                                  for i in itertools.count(1))
        self._loading_id = 1
        self._loaded_images = []

    def download(self, url):
        """Downloads the content of the URL, and returns it as bytes.

        This method is called whenever the soup contains an ``<img>`` or
        something else that has to be read from a file or downloaded. If it
        raises an exception, the ``alt`` of the ``<img>`` will be displayed
        instead of the actual image, if there is an ``alt``. The ``alt`` is
        also displayed while this method is running.

        By default, this uses :func:`urllib.request.urlopen`. You can override
        this if ``urllib`` is doing something dumb or you want to control which
        things can be downloaded.

        Usually this is called from some other thread than the main thread.
        """
        with urllib.request.urlopen(url) as response:
            return response.read()

    @teek.make_thread_safe
    def stop_loading(self, cleanup=True):
        """Tell currently running threads to do nothing to the :attr:`widget`.

        Things like ``<img>`` elements are loaded with threads, so they might
        add something to the text widget several seconds after the
        :meth:`add_soup` call.

        If ``cleanup`` is ``True``, this method also e.g. deletes already
        loaded images, because then it assumes that they are not needed
        anymore. This means that if you don't pass ``cleanup=False``, you
        should clear the text widget after calling this method.

        This is automatically called with ``cleanup=True`` when the
        :attr:`widget` is destroyed.
        """
        self._loading_id += 1
        if cleanup:
            while self._loaded_images:
                self._loaded_images.pop().delete()

    def create_tags(self):
        """
        Adds :ref:`text tags <textwidget-tags>` to the :attr:`widget` for
        displaying the soup elements.

        This is not called automatically; you should call this before actually
        using the ``SoupViewer``.

        Each text tag is named with ``'soup-'`` followed by the name of the
        corresponding HTML tag, such as ``'soup-p'`` or ``'soup-pre'``. If you
        are not happy with what this method does, you can change the text tags
        after calling it.
        """
        monospace_family = teek.NamedFont('TkFixedFont').family
        family = self.widget.config['font'].family
        basic_size = self.widget.config['font'].size     # may be negative
        h_sizes = {
            'h1': round(2.5 * basic_size),
            'h2': round(2.0 * basic_size),
            'h3': round(1.6 * basic_size),
            'h4': round(1.45 * basic_size),
            'h5': round(1.25 * basic_size),
            'h6': round(1.1 * basic_size),
        }

        # because pep8 line length
        tag = self.widget.get_tag

        # these tags don't need any special settings, but they need to be
        # created to avoid warnings in soup2teek
        tag('soup-p')
        tag('soup-ol')
        tag('soup-ul')

        # there's no soup-a because teek.extras.links handles that
        tag('soup-code')['font'] = (monospace_family, basic_size, '')
        tag('soup-pre')['font'] = (monospace_family, basic_size, '')
        tag('soup-pre')['lmargin1'] = 30
        tag('soup-pre')['lmargin2'] = 50
        tag('soup-li')['lmargin1'] = 10
        tag('soup-li')['lmargin2'] = 10
        tag('soup-strong')['font'] = (family, basic_size, 'bold')
        tag('soup-b')['font'] = (family, basic_size, 'bold')
        tag('soup-em')['font'] = (family, basic_size, 'italic')
        tag('soup-i')['font'] = (family, basic_size, 'italic')
        for h, size in h_sizes.items():
            tag('soup-' + h)['font'] = (family, size, 'bold')

        # make sure that html_pre's indenting stuff works inside list elements
        tag('soup-li').lower('soup-pre')

    def add_soup(self, element):
        """Render a BeautifulSoup4 HTML element.

        The text, images, or whatever the element represents are added to the
        end of the text widget.

        This method looks for methods whose names are ``handle_`` followed by
        the name of a HTML tag; for example, ``handle_h1()`` or ``handle_p()``.
        Those methods run when an element with the corresponding tag name is
        added. You can subclass :class:`SoupViewer` and create more of these
        methods to handle more different kinds of tags. There are two things
        that the methods can do:

        1. The method can return None to indicate that :meth:`add_soup`
           shouldn't do anything with the content of the element.

           ::

                def handle_pre(self, pre):
                    self.widget.insert(self.widget.end, pre.text.rstrip() + '\
\\n\\n')

        2. The method can be decorated with :func:`contextlib.contextmanager`.
           When it yields, :meth:`add_soup` will loop over the element and call
           itself recursively with each subelement.

           ::

                @contextlib.contextmanager
                def handle_ul(self, ul):
                    for li in ul:
                        if li.name == 'li':
                            # '\\N{bullet} ' creates a Unicode black circle ch\
aracter
                            li.insert(0, '\\N{bullet} ')
                    yield     # the content of the ul is added here
                    self.widget.insert(self.widget.end, '\\n')

        In either case, :meth:`add_soup` adds a
        :ref:`textwidget tag <textwidget-tags>` as explained in
        :meth:`create_tags`.
        """
        # beautifulsoup is buggy, sometimes this recurses infinitely and
        # sometimes this raises AttributeError
        #
        # see handle_ul() for an example of how this would be nice, if this
        # worked
        #element = copy.deepcopy(element)

        if element.name is None:
            # plain text, handle it kind of like web browsers do
            # \xa0 is non-breaking space
            text = str(element)
            text = re.sub(r'[^\S\xa0]+', ' ', text)

            last_char = self.widget.get(
                self.widget.end.back(chars=1), self.widget.end)
            if last_char.isspace():
                text = text.lstrip(' ')

            self.widget.insert(self.widget.end, text)
            return

        try:
            handler = getattr(self, 'handle_' + element.name)
        except AttributeError:
            omg = ("soup contains a <%s> tag, but %s has no handle_%s() method"
                   % (element.name, type(self).__name__, element.name))
            warnings.warn(omg, RuntimeWarning)
            handler = self._fallback_handler

        old_end = self.widget.end

        handler_result = handler(element)
        if handler_result is not None:
            with handler_result:
                for sub in element:
                    self.add_soup(sub)

        self.widget.get_tag('soup-' + element.name).add(
            old_end, self.widget.end)

    @contextlib.contextmanager
    def _fallback_handler(self, element):
        yield

    def handle_pre(self, element):
        self.widget.insert(self.widget.end, element.text.rstrip() + '\n\n')

    def handle_br(self, element):
        self.widget.insert(self.widget.end, '\n')

    @contextlib.contextmanager
    def _do_nothing_handler(self, element):
        yield

    handle_i = handle_em = _do_nothing_handler
    handle_b = handle_strong = _do_nothing_handler
    handle_code = _do_nothing_handler

    @contextlib.contextmanager
    def _double_newline_handler(self, element):
        yield
        self.widget.insert(self.widget.end, '\n\n')

    handle_h1 = _double_newline_handler
    handle_h2 = _double_newline_handler
    handle_h3 = _double_newline_handler
    handle_h4 = _double_newline_handler
    handle_h5 = _double_newline_handler
    handle_h6 = _double_newline_handler
    handle_p = _double_newline_handler

    @contextlib.contextmanager
    def handle_ul(self, element):
        for li in element:
            if li.name == 'li':
                li.insert(0, '\N{bullet} ')
        yield
        self.widget.insert(self.widget.end, '\n')

    @contextlib.contextmanager
    def handle_ol(self, element):
        for num, li in enumerate((sub for sub in element if sub.name == 'li'),
                                 start=1):
            li.insert(0, str(num) + '. ')
        yield
        self.widget.insert(self.widget.end, '\n')

    @contextlib.contextmanager
    def handle_li(self, element):
        yield
        last_char = self.widget.get(self.widget.end.back(chars=1))
        if last_char != '\n':
            self.widget.insert(self.widget.end, '\n')

    @contextlib.contextmanager
    def handle_a(self, element):
        start = self.widget.end
        yield
        end = self.widget.end
        links.add_url_link(self.widget, element.attrs['href'], start, end)

    @contextlib.contextmanager
    def handle_img(self, element):
        loading_id = self._loading_id

        mark_name = next(self._image_mark_names)

        # TODO: add 'mark gravity' to teek
        self.widget.marks[mark_name + '-start'] = self.widget.end
        teek.tcl_call(None, self.widget, 'mark', 'gravity',
                      mark_name + '-start', 'left')

        self.widget.insert(self.widget.end, element.attrs.get('alt', ''))

        self.widget.marks[mark_name + '-end'] = self.widget.end
        teek.tcl_call(None, self.widget, 'mark', 'gravity',
                      mark_name + '-end', 'left')

        if self._use_threads:
            # daemon=True because i don't care wtf happens to this thread
            threading.Thread(
                target=self._image_loader_thread,
                args=[mark_name, element.attrs['src'], loading_id],
                daemon=True).start()

        yield

    def _image_loader_thread(self, mark_name, src, loading_id):
        bytez = self.download(src)
        if loading_id == self._loading_id:
            self._add_image(mark_name, bytez)

    # only one of these will be running at a time, because the decoration
    @teek.make_thread_safe
    def _add_image(self, mark_name, bytez):
        image = image_loader.from_bytes(bytez)
        self._loaded_images.append(image)
        start_pos = self.widget.marks[mark_name + '-start']
        end_pos = self.widget.marks[mark_name + '-end']

        tags = self.widget.get_all_tags(start_pos)
        self.widget.delete(start_pos, end_pos)

        teek.tcl_call(None, self.widget, 'image', 'create', start_pos,
                      '-image', image)
        for tag in tags:
            tag.add(start_pos, start_pos.forward(chars=1))
