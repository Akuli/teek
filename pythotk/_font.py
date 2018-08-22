import itertools

from ._tcl_calls import call as tcl_call
from . import TclError

_flatten = itertools.chain.from_iterable


def _font_property(type_spec, option):

    def getter(self):
        return tcl_call(type_spec, "font", "actual", self, "-" + option)

    def setter(self, value):
        if not isinstance(self, NamedFont):
            raise AttributeError(
                "cannot change options of non-named fonts, but you can use "
                "the_font.to_named_font() to create a mutable font object")
        tcl_call(None, "font", "configure", self, "-" + option, value)

    return property(getter, setter)


def _anonymous_font_new_helper(font_description):
    # magic: Font(a_font_name) returns a NamedFont
    # is the font description a font name? configure works only with
    # font names, not other kinds of font descriptions
    try:
        tcl_call(None, 'font', 'configure', font_description)
    except TclError:
        return None

    # it is a font name
    return NamedFont(font_description)


class Font:

    def __new__(cls, *args, **kwargs):
        if not issubclass(cls, NamedFont):     # Font, but not NamedFont
            named_font = _anonymous_font_new_helper(*args, **kwargs)
            if named_font is not None:
                return named_font

        return super(Font, cls).__new__(cls)

    def __init__(self, font_description):
        # the _font_description of NamedFont is the font name
        self._font_description = font_description

    family = _font_property(str, 'family')
    size = _font_property(int, 'size')
    weight = _font_property(str, 'weight')
    slant = _font_property(str, 'slant')
    underline = _font_property(bool, 'underline')
    overstrike = _font_property(bool, 'overstrike')

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._font_description)

    def __eq__(self, other):
        if not isinstance(other, Font):
            return False
        return self._font_description == other._font_description

    def __hash__(self):
        return hash(self._font_description)

    @classmethod
    def from_tcl(cls, font_description):
        return cls(font_description)

    def to_tcl(self):
        return self._font_description

    def measure(self, text):
        return tcl_call(int, "font", "measure", self, text)

    def metrics(self):
        result = tcl_call(
            {"-ascent": int, "-descent": int,
             "-linespace": int, "-fixed": bool},
            "font", "metrics", self)
        return {name.lstrip('-'): value for name, value in result.items()}

    def to_named_font(self):
        options = tcl_call({}, 'font', 'actual', self)
        kwargs = {name.lstrip('-'): value for name, value in options.items()}
        return NamedFont(**kwargs)

    @classmethod
    def families(self):
        result = tcl_call([str], "font", "families")

        # windows has weird fonts that start with @, and i have never seen them
        # being actually used for something, but i have seen filtering them
        # out a lot so i thought i might as well do it here
        return [family for family in result if not family.startswith('@')]


class NamedFont(Font):

    def __init__(self, name=None, **kwargs):
        options_with_dashes = []
        for option_name, value in kwargs.items():
            options_with_dashes.extend(['-' + option_name, value])

        if name is None:
            # let tk choose a name that's not used yet
            name = tcl_call(str, 'font', 'create', *options_with_dashes)
        else:
            # do we need to create a font with the given name?
            try:
                tcl_call(None, 'font', 'create', name, *options_with_dashes)
            except TclError:
                # no, it exists already, but we must do something with the
                # options
                tcl_call(None, 'font', 'configure', name, *options_with_dashes)

        super().__init__(name)

    # __repr__, __eq__, __hash__, and event to_named_font, {from,to}_tcl are
    # fine, to_named_font creates a copy of this font

    # TODO: rename this less verbosely if it's possible while keeping the
    #       meaning obvious
    @classmethod
    def get_all_named_fonts(cls):
        return list(map(cls, tcl_call([str], 'font', 'names')))

    def delete(self):
        tcl_call(None, "font", "delete", self)
