import collections.abc
import functools

import pythotk as tk
from pythotk._widgets import ConfigDict, ChildMixin, Widget


# a new subclass of this is created for each text widget, and inheriting
# from namedtuple makes comparing the text indexes work nicely
class _IndexBase(collections.namedtuple('TextIndex', 'line column')):
    _widget = None

    def to_tcl(self):
        return '%d.%d' % self       # lol, magicz

    @classmethod
    def _from_string(cls, string):
        # tk text widgets have an implicit and invisible newline character
        # at the end of them, and i always ignore it everywhere by using
        # 'end - 1 char' instead of 'end'
        string = cls._widget._call(str, cls._widget, 'index', string)
        after_stupid_newline = cls._widget._call(
            str, cls._widget, 'index', 'end')

        if string == after_stupid_newline:
            return cls._widget.end
        return cls(*map(int, string.split('.')))

    def forward(self, *, chars=0, indices=0, lines=0):
        result = '%s %+d lines %+d chars %+d indices' % (
            self.to_tcl(), lines, chars, indices)
        return type(self)._from_string(result)

    def back(self, *, chars=0, indices=0, lines=0):
        return self.forward(chars=-chars, indices=-indices, lines=-lines)

    def _apply_suffix(self, suffix):
        return type(self)._from_string('%s %s' % (self.to_tcl(), suffix))

    linestart = functools.partialmethod(_apply_suffix, 'linestart')
    lineend = functools.partialmethod(_apply_suffix, 'lineend')
    wordstart = functools.partialmethod(_apply_suffix, 'wordstart')
    wordend = functools.partialmethod(_apply_suffix, 'wordend')


class _Tag(ConfigDict):

    def __init__(self, widget, name):
        self._widget = widget
        self.name = name
        super().__init__(self._call_tag_subcommand)
        dict(self)      # TODO: why do tests fail without this?

        # these are from text(3tk)
        # pixels options are usually integers, but they are strings because
        # they can also be e.g. 1i instead, see man page
        for prefix in ['', 'select']:
            self._types[prefix + 'foreground'] = tk.Color
            self._types[prefix + 'background'] = tk.Color

        self._types['elide'] = bool
        #self._types['font'] = ???
        #self._types['justify'] = ??? enum left,right,center
        self._types['lmargoncolor'] = self._types['rmargoncolor'] = tk.Color
        self._types['overstrike'] = bool
        #self._types['tabs'] = ???
        #self._types['tabstyle'] = ??? enum tabular,wordprocessor
        self._types['underline'] = bool
        self._types['underlinefg'] = tk.Color
        #self._types['wrap'] = ??? enum none,char,word

    def __repr__(self):
        return '<Text widget tag %r>' % self.name

    def to_tcl(self):
        return self.name

    # this inserts self between the arguments, that's why it's needed
    def _call_tag_subcommand(self, returntype, subcommand, *args):
        return self._widget._call(
            returntype, self._widget, 'tag', subcommand, self, *args)

    def __eq__(self, other):
        if not isinstance(other, _Tag):
            return NotImplemented
        return self._widget is other._widget and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add(self, index1, index2):
        index1 = self._widget.index(*index1)
        index2 = self._widget.index(*index2)
        return self._call_tag_subcommand(None, 'add', index1, index2)

    # TODO: bind

    def delete(self):
        self._call_tag_subcommand(None, 'delete')

    # TODO: tests
    def _prevrange_or_nextrange(self, prev_or_next, index1, index2=None):
        index1 = self._widget.index(*index1)
        if index2 is None:
            index2 = {'prev': self._widget.start,
                      'next': self._widget.end}[prev_or_next]
        else:
            index2 = self._widget.index(*index2)

        strings = self._call_tag_subcommand(
            [str], prev_or_next + 'range', index1, index2)
        if not strings:
            # the tcl command returned '', no ranges found
            return None

        string1, string2 = strings
        return (self._widget._TextIndex._from_string(string1),
                self._widget._TextIndex._from_string(string2))

    prevrange = functools.partialmethod(_prevrange_or_nextrange, 'prev')
    nextrange = functools.partialmethod(_prevrange_or_nextrange, 'next')

    def ranges(self):
        flat_pairs = map(self._widget._TextIndex._from_string,
                         self._call_tag_subcommand([str], 'ranges'))

        # magic to convert a flat iterator to pairs: a,b,c,d --> (a,b), (c,d)
        return list(zip(flat_pairs, flat_pairs))

    def remove(self, index1=None, index2=None):
        widget = self._widget       # because pep8 line length
        index1 = widget.start if index1 is None else widget.index(*index1)
        index2 = widget.end if index2 is None else widget.index(*index2)
        self._call_tag_subcommand(None, 'remove', index1, index2)


class _Marks(collections.abc.MutableMapping):

    def __init__(self, widget):
        self._widget = widget

    def _get_name_list(self):
        return self._widget._call([str], self._widget, 'mark', 'names')

    def __iter__(self):
        return iter(self._get_name_list())

    def __len__(self):
        return len(self._get_name_list())

    def __setitem__(self, name, index):
        index = self._widget.index(*index)
        self._widget._call(None, self._widget, 'mark', 'set', name, index)

    def __getitem__(self, name):
        if name not in self._get_name_list():
            raise KeyError(name)

        index_string = self._widget._call(str, self._widget, 'index', name)
        return self._widget._TextIndex._from_string(index_string)

    def __delitem__(self, name):
        self._widget._call(None, self._widget, 'mark', 'unset', name)


class Text(ChildMixin, Widget):
    r"""This is the text widget.

    .. attribute:: start
    .. attribute:: end

        :ref:`Index objects <textwidget-index>` that represents the start and
        end of the text.

        .. tip::
            Use ``textwidget.end.line`` to count the number of lines of text
            in the text widget.

        Note that this changes when the text widget's content changes:

        >>> text = tk.Text(window)
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
        of just ``end``. **Pythotk doesn't do that** because 99% of the
        time it's not useful and 1% of the time it's confusing to people
        reading the code, so ``text.get(text.start, text.end)`` doesn't
        return anything that is not visible in the text widget.
    """

    def __init__(self, parent, **kwargs):
        super().__init__('text', parent, **kwargs)
        self._TextIndex = type(
            'TextIndex', (_IndexBase,), {'_widget': self})
        self._tag_objects = {}
        self.marks = _Marks(self)

    def _repr_parts(self):
        return ['contains %d lines of text' % self.end.line]

    def get_tag(self, name):
        """Return a tag object by name, or create a new if needed."""
        try:
            return self._tag_objects[name]
        except KeyError:
            tag = _Tag(self, name)
            self._tag_objects[name] = tag
            return tag

    def get_all_tags(self, index=None):
        """Return all tags as tag objects.

        See ``pathName tag names`` in :man:`text(3tk)` for more details.
        """
        args = [self, 'tag', 'names']
        if index is not None:
            args.append(self.index(*index))
        return [self.get_tag(name) for name in self._call([str], *args)]

    @property
    def start(self):
        return self.index(1, 0)

    @property
    def end(self):
        index_string = self._call(str, self, 'index', 'end - 1 char')
        return self.index(*map(int, index_string.split('.')))

    def index(self, line, column):
        """Create an index object from line and column integers.

        If the specified index does not exist in the text widget, the nearest
        existing index is used instead, as is typical in Tk.
        """
        return self._TextIndex._from_string('%d.%d' % (line, column))

    def get(self, index1=None, index2=None):
        """Return text in the widget.

        If the indexes are not given, they default to the beginning and end of
        the text widget, respectively.
        """
        index1 = self.start if index1 is None else self.index(*index1)
        index2 = self.end if index2 is None else self.index(*index2)
        return self._call(str, self, 'get', index1, index2)

    def insert(self, index, text, tag_list=()):
        """Add text to the widget.

        The ``tag_list`` can be any iterable of tag name strings or tag
        objects.
        """
        index = self.index(*index)
        self._call(None, self, 'insert', index, text, tag_list)

    def replace(self, index1, index2, new_text, tag_list=()):
        """See :man:`text(3tk)` and :meth:`insert`."""
        index1, index2 = self.index(*index1), self.index(*index2)
        self._call(None, self, 'replace', index1, index2, new_text, tag_list)
