import itertools

from ._tcl_calls import call as tcl_call
from . import TclError

_flatten = itertools.chain.from_iterable


def _font_configure_property(attribute):
    def getter(self):
        ty = self._OPTIONS_TYPE["-" + attribute]
        return tcl_call(ty, "font", "configure", self.name, "-" + attribute)

    def setter(self, value):
        tcl_call(None, "font", "configure", self.name, "-" + attribute, value)

    return property(getter, setter)


class Font:
    # XXX: Akuli, please add docs.
    _OPTIONS_TYPE = {
        "-family": str,
        "-size": int,
        "-weight": str,
        "-slant": str,
        "-underline": bool,
        "-overstrike": bool,
    }

    # self.description is a "font description", see manual page

    # TODO: Font('Helvetica') does the wrong thing, change this somehow?
    def __init__(self, name=None, **kwargs):
        options = list(_flatten(('-' + option, value)
                                for option, value in kwargs.items()))
        if name is None:
            # let tk choose a name that's not used yet
            self.name = tcl_call(str, "font", "create", *options)
        else:
            self.name = name
            try:
                tcl_call(None, "font", "create", name, *options)
            except TclError:
                # font exists, update the options to it
                tcl_call(None, "font", "configure", name, *options)

    @classmethod
    def from_tcl(cls, font_description):
        # is the font description a name of a font?
        try:
            tcl_call(None, 'font', 'configure', font_description)
        except TclError:
            # no, it is one of the other font description kinds in font(3tk)
            # {} is a dict with all names and values strings
            # TODO: avoid creating a new named font?
            actual = tcl_call({}, 'font', 'actual', font_description)
            return cls(**{name.lstrip('-'): value
                          for name, value in actual.items()})

        # yes, the description is a font name
        result = cls.__new__(cls)   # create a new object without __init__
        result.name = font_description
        return result

    def to_tcl(self):
        return self.name

    family = _font_configure_property("family")
    size = _font_configure_property("size")
    weight = _font_configure_property("weight")
    slant = _font_configure_property("slant")
    underline = _font_configure_property("underline")
    overstrike = _font_configure_property("overstrike")

    def actual(self):
        dashed = tcl_call(self._OPTIONS_TYPE, "font", "actual", self.name)
        return {name.lstrip('-'): value for name, value in dashed.items()}

    def delete(self):
        # deleting a font object that represents a non-name description
        # does nothing
        if self._description_is_name():
            tcl_call(None, "font", "delete", self.name)

    def measure(self, text):
        return tcl_call(int, "font", "measure", self.name, text)

    def metrics(self):
        return tcl_call(
            {"ascent": int, "descent": int, "linespace": int, "fixed": bool},
            "font",
            "metrics",
        )

    @classmethod
    def families(self):
        return tcl_call([str], "font", "families")

    @classmethod
    def names(self):
        return tcl_call([str], "font", "names")

    def __repr__(self):
        return (
            "%s("
            "name=%s,"
            "family=%s,"
            "size=%s,"
            "weight=%s,"
            "slant=%s,"
            "underline=%s,"
            "overstrike=%s"
            ")"
        ) % (
            self.__class__.__name__,
            self.name,
            self.family,
            self.size,
            self.weight,
            self.slant,
            self.underline,
            self.overstrike,
        )

    def __eq__(self, other):
        if not isinstance(other, Font):
            return NotImplemented
        return self.name == other.name

    # make font objects hashable, defining an __eq__ undefines __hash__
    def __hash__(self):
        return hash(self.name)
