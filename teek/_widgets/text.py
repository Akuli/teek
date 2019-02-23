import collections.abc
import functools
import re

import teek
from teek._structures import CgetConfigureConfigDict
from teek._tcl_calls import make_thread_safe
from teek._widgets.base import BindingDict, ChildMixin, Widget


# a new subclass of IndexBase is created for each text widget, and inheriting
# from namedtuple makes comparing the text indexes work nicely
class IndexBase(collections.namedtuple('TextIndex', 'line column')):
    _widget = None

    def to_tcl(self):
        return '%d.%d' % self       # lol, magicz

    @classmethod
    @make_thread_safe
    def from_tcl(cls, string):
        # the returned index may be out of bounds ONLY IF it doesn't contain
        # anything more fancy than 'line.column'
        if re.fullmatch(r'(\d+)\.(\d+)', string) is None:
            string = cls._widget._call(str, cls._widget, 'index', string)

            # hide the invisible newline that tk wants to have at the end
            tk_fake_end = cls._widget._call(str, cls._widget, 'index', 'end')
            if string == tk_fake_end:
                return cls._widget.end

        return cls(*map(int, string.split('.')))

    @make_thread_safe
    def between_start_end(self):
        if self < self._widget.start:
            return self._widget.start
        if self > self._widget.end:
            return self._widget.end
        return self

    def forward(self, *, chars=0, indices=0, lines=0):
        result = '%s %+d lines %+d chars %+d indices' % (
            self.to_tcl(), lines, chars, indices)
        return type(self).from_tcl(result).between_start_end()

    def back(self, *, chars=0, indices=0, lines=0):
        return self.forward(chars=-chars, indices=-indices, lines=-lines)

    def _apply_suffix(self, suffix):
        return type(self).from_tcl(
            '%s %s' % (self.to_tcl(), suffix)).between_start_end()

    linestart = functools.partialmethod(_apply_suffix, 'linestart')
    lineend = functools.partialmethod(_apply_suffix, 'lineend')
    wordstart = functools.partialmethod(_apply_suffix, 'wordstart')
    wordend = functools.partialmethod(_apply_suffix, 'wordend')


class Tag(CgetConfigureConfigDict):

    def __init__(self, widget, name):
        self._widget = widget
        self.name = name
        super().__init__(self._call_tag_subcommand)

        self._types.update({
            'background': teek.Color,
            #'bgstipple': ???,
            'borderwidth': teek.ScreenDistance,
            'elide': bool,
            #'fgstipple': ???,
            'font': teek.Font,
            'foreground': teek.Color,
            'justify': str,
            'lmargin1': teek.ScreenDistance,
            'lmargin2': teek.ScreenDistance,
            'lmargin3': teek.ScreenDistance,
            'lmargincolor': teek.Color,
            'offset': teek.ScreenDistance,
            'overstrike': bool,
            'overstrikefg': teek.Color,
            'relief': str,
            'rmargin': teek.ScreenDistance,
            'rmargincolor': teek.Color,
            'selectbackground': teek.Color,
            'selectforeground': teek.Color,
            'spacing1': teek.ScreenDistance,
            'spacing2': teek.ScreenDistance,
            'spacing3': teek.ScreenDistance,
            'tabs': [str],
            'tabstyle': str,
            'underline': bool,
            'underlinefg': teek.Color,
            'wrap': str,
        })

        self.bindings = BindingDict(self._call_bind, widget.command_list)
        self.bind = self.bindings._convenience_bind

    def __repr__(self):
        return '<Text widget tag %r>' % self.name

    def to_tcl(self):
        return self.name

    # this inserts self between the arguments, that's why it's needed
    def _call_tag_subcommand(self, returntype, subcommand, *args):
        return self._widget._call(
            returntype, self._widget, 'tag', subcommand, self, *args)

    def _call_bind(self, returntype, *args):
        return self._call_tag_subcommand(returntype, 'bind', *args)

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return NotImplemented
        return self._widget is other._widget and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @make_thread_safe
    def add(self, index1, index2):
        index1 = self._widget._get_index_obj(index1)
        index2 = self._widget._get_index_obj(index2)
        return self._call_tag_subcommand(None, 'add', index1, index2)

    # TODO: bind

    def delete(self):
        self._call_tag_subcommand(None, 'delete')

    @make_thread_safe
    def _prevrange_or_nextrange(self, prev_or_next, index1, index2=None):
        index1 = self._widget._get_index_obj(index1)
        if index2 is None:
            index2 = {'prev': self._widget.start,
                      'next': self._widget.end}[prev_or_next]
        else:
            index2 = self._widget._get_index_obj(index2)

        results = self._call_tag_subcommand(
            [self._widget.TextIndex], prev_or_next + 'range', index1, index2)
        if not results:
            # the tcl command returned "", no ranges found
            return None

        index1, index2 = results
        return (index1.between_start_end(), index2.between_start_end())

    prevrange = functools.partialmethod(_prevrange_or_nextrange, 'prev')
    nextrange = functools.partialmethod(_prevrange_or_nextrange, 'next')

    @make_thread_safe
    def ranges(self):
        flat_pairs = map(self._widget.TextIndex.from_tcl,
                         self._call_tag_subcommand([str], 'ranges'))

        # magic to convert a flat iterator to pairs: a,b,c,d --> (a,b), (c,d)
        return list(zip(flat_pairs, flat_pairs))

    @make_thread_safe
    def remove(self, index1=None, index2=None):
        if index1 is None:
            index1 = self._widget.start
        else:
            index1 = self._widget._get_index_obj(index1)

        if index2 is None:
            index2 = self._widget.end
        else:
            index2 = self._widget._get_index_obj(index2)

        self._call_tag_subcommand(None, 'remove', index1, index2)

    @make_thread_safe
    def _lower_or_raise(self, lower_or_raise, other_tag=None):
        if other_tag is None:
            self._call_tag_subcommand(None, lower_or_raise)
        else:
            self._call_tag_subcommand(None, lower_or_raise, other_tag)

    lower = functools.partialmethod(_lower_or_raise, 'lower')
    raise_ = functools.partialmethod(_lower_or_raise, 'raise')


class MarksDict(collections.abc.MutableMapping):

    def __init__(self, widget):
        self._widget = widget

    def _get_name_list(self):
        return self._widget._call([str], self._widget, 'mark', 'names')

    def __iter__(self):
        return iter(self._get_name_list())

    def __len__(self):
        return len(self._get_name_list())

    @make_thread_safe
    def __setitem__(self, name, index):
        index = self._widget._get_index_obj(index)
        self._widget._call(None, self._widget, 'mark', 'set', name, index)

    @make_thread_safe
    def __getitem__(self, name):
        if name not in self._get_name_list():
            raise KeyError(name)

        result = self._widget._call(
            self._widget.TextIndex, self._widget, 'index', name)
        return result.between_start_end()

    def __delitem__(self, name):
        self._widget._call(None, self._widget, 'mark', 'unset', name)


class Text(ChildMixin, Widget):
    r"""This is the text widget.

    Manual page: :man:`text(3tk)`

    .. attribute:: start
                   end

        :ref:`TextIndex objects <textwidget-index>` that represents the start
        and end of the text.

        .. tip::
            Use ``textwidget.end.line`` to count the number of lines of text
            in the text widget.

        Note that ``end`` changes when the text widget's content changes:

        >>> window = teek.Window()
        >>> text = teek.Text(window)
        >>> text.end
        TextIndex(line=1, column=0)
        >>> old_end = text.end
        >>> text.insert(text.end, 'hello')
        >>> text.end
        TextIndex(line=1, column=5)
        >>> old_end
        TextIndex(line=1, column=0)
        >>> text.get(old_end, text.end)
        'hello'

        Tk has a concept of an invisible newline character at the end of
        the widget. In pure Tcl or in tkinter, getting the text from
        beginning to ``end`` returns the text in the widget plus a ``\n``,
        which is why you almost always need to do ``end - 1 char`` instead
        of just ``end``. **Teek doesn't do that** because 99% of the
        time it's not useful and 1% of the time it's confusing to people
        reading the code, so ``text.get(text.start, text.end)`` doesn't
        return anything that is not visible in the text widget.

    .. attribute:: marks

        A dictionary-like object with mark names as keys and
        :ref:`index objects <textwidget-index>` as values. See
        :ref:`textwidget-marks`.

    .. method:: xview(*args)
                yview(*args)

        These call ``pathName xview`` and ``pathName yview`` as documented in
        :man:`text(3tk)`. Pass string arguments to these methods to invoke the
        subcommands. For example, ``text_widget.yview('moveto', 1)`` scrolls to
        end vertically.

        If no arguments are given, these methods return a two-tuple of floats
        (see the manual page); otherwise, None is returned.
    """

    _widget_name = 'text'
    tk_class_name = 'Text'

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.TextIndex = type(     # creates a new subclass of IndexBase
            'TextIndex', (IndexBase,), {'_widget': self})
        self._tag_objects = {}
        self.marks = MarksDict(self)

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'autoseparators': bool,
            'blockcursor': bool,
            'endline': int,
            # undocumented: height can also be a screen distance??
            # probably a bug
            'height': int,
            'inactiveselectbackground': teek.Color,
            'insertunfocussed': str,
            'maxundo': int,
            'spacing1': teek.ScreenDistance,
            'spacing2': teek.ScreenDistance,
            'spacing3': teek.ScreenDistance,
            'startline': int,
            'state': str,
            'tabs': [str],
            'tabstyle': str,
            'undo': bool,
            'width': int,
            'wrap': str,
        })

    def _repr_parts(self):
        return ['contains %d lines of text' % self.end.line]

    def _get_index_obj(self, index):
        if isinstance(index, str):
            raise TypeError(
                "string indexes are not supported, use (line, column) int "
                "tuples or TextIndex objects instead")

        return self.TextIndex(*index).between_start_end()

    @make_thread_safe
    def get_tag(self, name):
        """Return a tag object by name, creating a new one if needed."""
        try:
            return self._tag_objects[name]
        except KeyError:
            tag = Tag(self, name)

            # this actually creates the tag so that it shows up in
            # get_all_tags()
            self._call(None, self, 'tag', 'configure', name)

            self._tag_objects[name] = tag
            return tag

    @make_thread_safe
    def get_all_tags(self, index=None):
        """Return all tags as tag objects.

        See ``pathName tag names`` in :man:`text(3tk)` for more details.
        """
        args = [self, 'tag', 'names']
        if index is not None:
            args.append(self._get_index_obj(index))
        return [self.get_tag(name) for name in self._call([str], *args)]

    @property
    def start(self):
        return self.TextIndex(1, 0)

    @property
    def end(self):
        index_string = self._call(str, self, 'index', 'end - 1 char')
        return self.TextIndex(*map(int, index_string.split('.')))

    @make_thread_safe
    def get(self, index1=None, index2=None):
        """Return text in the widget.

        If the indexes are not given, they default to the beginning and end of
        the text widget, respectively.
        """
        if index1 is None:
            index1 = self.start
        else:
            index1 = self._get_index_obj(index1)

        if index2 is None:
            index2 = self.end
        else:
            index2 = self._get_index_obj(index2)

        return self._call(str, self, 'get', index1, index2)

    @make_thread_safe
    def insert(self, index, text, tag_list=()):
        """Add text to the widget.

        The ``tag_list`` can be any iterable of tag name strings or tag
        objects.
        """
        index = self._get_index_obj(index)
        self._call(None, self, 'insert', index, text, tag_list)

    @make_thread_safe
    def replace(self, index1, index2, new_text, tag_list=()):
        """See :man:`text(3tk)` and :meth:`insert`."""
        self._call(None, self, 'replace', self._get_index_obj(index1),
                   self._get_index_obj(index2), new_text, tag_list)

    def delete(self, index1, index2):
        """See :man:`text(3tk)` and :meth:`insert`."""
        self._call(None, self, 'delete',
                   self._get_index_obj(index1), self._get_index_obj(index2))

    def see(self, index):
        """Scroll so that an index is visible.

        See :man:`text(3tk)` for details.
        """
        self._call(None, self, 'see', self._get_index_obj(index))

    def _xview_or_yview(self, xview_or_yview, *args):
        if not args:
            return self._call((float, float), self, xview_or_yview)

        self._call(None, self, xview_or_yview, *args)
        return None

    xview = functools.partialmethod(_xview_or_yview, 'xview')
    yview = functools.partialmethod(_xview_or_yview, 'yview')
