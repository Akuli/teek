import collections.abc
import functools

import teek
from teek._widgets.base import Widget, ChildMixin
from teek._structures import CgetConfigureConfigDict


# you can also make a list of canvas items instead of tagging, but there are
# things that are much easier with good support for tags, like bbox of multiple
# canvas items
#
# TODO: how are these different from item.config['tags']?
#       which is better? or are they equivalent in all the possible ways?
class Tags(collections.abc.MutableSet):

    def __init__(self, item):
        self._item = item

    def _gettags(self):
        return self._item.canvas._call(
            [str], self._item.canvas, 'gettags', self._item)

    def __iter__(self):
        return iter(self._gettags())

    def __contains__(self, tag):
        return tag in self._gettags()

    def __len__(self):
        return len(self._gettags())

    def add(self, tag):
        self._item.canvas._call(
            None, self._item.canvas, 'addtag', tag, 'withtag', self._item)

    def discard(self, tag):
        self._item._call(None, 'dtag', self._item, tag)


class CanvasItem:

    # a 'canvas' attribute is added in subclasses

    # __new__ magic ftw
    def __init__(self, *args, **kwargs):
        raise TypeError(
            "don't create canvas.Item objects yourself, use methods like "
            "create_line(), create_rectangle() etc instead")

    def _create(self, type_string, *coords, **kwargs):
        id_ = self.canvas._call(
            str, self.canvas, 'create', type_string, *coords)
        self._setup(type_string, id_)
        self.config.update(kwargs)

    def __repr__(self):
        try:
            coords = self.coords
        except RuntimeError:
            return '<deleted %s canvas item>' % self.type_string
        return '<%s canvas item at %r>' % (self.type_string, coords)

    def _call(self, returntype, subcommand, *args):
        return self.canvas._call(
            returntype, self.canvas, subcommand, *args)

    def _config_caller(self, returntype, cget_or_configure, *args):
        return self._call(returntype, 'item' + cget_or_configure, self, *args)

    def _setup(self, type_string, id_):
        self.type_string = type_string
        self._id = id_

        self.tags = Tags(self)
        self.config = CgetConfigureConfigDict(self._config_caller)

        prefixed = {
            #'stipple': ???,
            #'outlinestipple': ???,
            'fill': teek.Color,
            'outline': teek.Color,
            'dash': str,
            # TODO: support non-float coordinates? see COORDINATES in man page
            'width': float,
        }
        for prefix in ['', 'active', 'disabled']:
            self.config._types.update({
                prefix + key: value for key, value in prefixed.items()})

        self.config._types.update({
            'offset': str,
            'outlineoffset': str,
            'joinstyle': str,
            'splinesteps': int,
            'smooth': str,
            'state': str,
            'tags': [str],
            'capstyle': str,
            'arrow': str,
            # see comment about floats in prefixed
            'dashoffset': float,
            'arrowshape': (float, float, float),
        })

    @classmethod
    def from_tcl(cls, id_):
        type_ = cls.canvas._call(str, cls.canvas, 'type', id_)
        item = cls.__new__(cls)     # create instance without calling __init__
        item._setup(type_, id_)
        return item

    def to_tcl(self):
        return self._id

    def __eq__(self, other):
        if isinstance(other, CanvasItem):
            return (self.canvas is other.canvas and
                    self._id == other._id)
        return NotImplemented

    def __hash__(self):
        return hash((self.canvas, self._id))

    @property
    def coords(self):
        result = self._call([float], 'coords', self)
        if not result:
            raise RuntimeError("the canvas item has been deleted")
        return tuple(result)

    @coords.setter
    def coords(self, coords):
        self._call(None, 'coords', self, *coords)

    def find_above(self):
        return self._call(self.canvas.Item, 'find', 'above', self)

    def find_below(self):
        return self._call(self.canvas.Item, 'find', 'below', self)

    # TODO: bind, dchars

    def delete(self):
        return self._call(None, 'delete', self)


# TODO: arc, bitmap, image, line, polygon, text, window


class Canvas(ChildMixin, Widget):
    """This is the canvas widget.

    Manual page: :man:`canvas(3tk)`

    .. method:: create_line(*x_and_y_coords, **kwargs)
                create_oval(x1, y1, x2, y2, **kwargs)
                create_rectangle(x1, y1, x2, y2, **kwargs)

        These create and return new :ref:`canvas items <canvas-items>`. See
        the appropriate sections of :man:`canvas(3tk)` for details, e.g.
        ``RECTANGLE ITEMS`` for ``create_rectangle()``.
    """

    _widget_name = 'canvas'
    tk_class_name = 'Canvas'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Item = type('Item', (CanvasItem,), {'canvas': self})

    def _init_config(self):
        super()._init_config()
        self.config._types.update({
            'xscrollincrement': teek.ScreenDistance,
            'yscrollincrement': teek.ScreenDistance,
            'offset': str,   # couldn't be bothered to make it different
            'closeenough': float,
            'confine': bool,
            # TODO: support non-float coordinates? see COORDINATES in man page
            'width': float,
            'height': float,
            'scrollregion': [float],
        })

    def _create(self, type_string, *coords, **kwargs):
        item = self.Item.__new__(self.Item)
        item._create(type_string, *coords, **kwargs)
        return item

    create_rectangle = functools.partialmethod(_create, 'rectangle')
    create_oval = functools.partialmethod(_create, 'oval')
    create_line = functools.partialmethod(_create, 'line')

    def find_all(self):
        """Returns a list of all items on the canvas."""
        return self._call([self.Item], self, 'find', 'all')

    def find_closest(self, x, y, *args):
        """Returns the canvas item that is closest to the given coordinates.

        See the ``closest`` documentation of ``pathName addtag`` in
        :man:`canvas(3tk)` for details.
        """
        return self._call(self.Item, self, 'find', 'closest', x, y, *args)

    def find_enclosed(self, x1, y1, x2, y2):
        """Returns a list of canvas items.

        See the ``enclosed`` documentation of ``pathName addtag`` in
        :man:`canvas(3tk)` for details.
        """
        return self._call(
            [self.Item], self, 'find', 'enclosed', x1, y1, x2, y2)

    def find_overlapping(self, x1, y1, x2, y2):
        """Returns a list of canvas items.

        See the ``enclosed`` documentation of ``pathName addtag`` in
        :man:`canvas(3tk)` for details.
        """
        return self._call(
            [self.Item], self, 'find', 'overlapping', x1, y1, x2, y2)

    def find_withtag(self, tag_name):
        """Returns a list of canvas items that have the given \
:ref:`tag <canvas-tags>`.

        The tag name is given as a string. See the ``enclosed`` documentation
        of ``pathName addtag`` in :man:`canvas(3tk)` for details.
        """
        return self._call([self.Item], self, 'find', 'withtag', tag_name)

    # TODO: canvasx canvasy
