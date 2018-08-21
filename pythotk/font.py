from ._tcl_calls import call as tcl_call, to_tcl, from_tcl
from . import TclError


def _tcl_options(py_options):
    tcl_options = []
    for k, v in py_options.items():
        tcl_options.append("-" + k)
        tcl_options.append(to_tcl(v))
    return tcl_options


def _remove_dashes(options):
    return {k.lstrip("-"): v for k, v in options.items()}


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

    def __init__(
        self,
        name=None,
        family=None,
        size=None,
        weight=None,
        slant=None,
        underline=None,
        overstrike=None,
    ):
        options = {}

        if family is not None:
            options["family"] = family

        if size is not None:
            options["size"] = size

        if weight is not None:
            options["weight"] = weight

        if slant is not None:
            options["slant"] = slant

        if underline is not None:
            options["underline"] = underline

        if overstrike is not None:
            options["overstrike"] = overstrike

        tcl_options = _tcl_options(options)

        if name is None:
            name = tcl_call(str, "font", "create", *tcl_options)
        else:
            try:
                tcl_call(None, "font", "create", name, *tcl_options)
            except TclError as e:
                # font exists
                pass

        self.name = name

    family = _font_configure_property("family")
    size = _font_configure_property("size")
    weight = _font_configure_property("weight")
    slant = _font_configure_property("slant")
    underline = _font_configure_property("underline")
    overstrike = _font_configure_property("overstrike")

    def actual(self):
        return _remove_dashes(
            tcl_call(self._OPTIONS_TYPE, "font", "actual", self.name)
        )

    def delete(self):
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
        return self.name == other.name

    @classmethod
    def from_tcl(cls, data):
        # Check if this is a font description in the form of an options list.
        try:
            options = from_tcl(cls._OPTIONS_TYPE, data)
            assert not (options.keys() - cls._OPTIONS_TYPE.keys())
        except (TclError, ValueError, AssertionError):
            pass
        else:
            return cls(**_remove_dashes(options))

        # Check if this is a font description in the form of
        # a "family size *styles" list.
        try:
            family, size, *styles = from_tcl([str], data)
        except (TclError, ValueError, AssertionError):
            pass
        else:
            weight = "normal"
            slant = "roman"
            underline = False
            overstrike = False

            for style in styles:
                if style == "normal":
                    weight = "normal"
                elif style == "bold":
                    weight = "bold"
                elif style == "roman":
                    slant = "roman"
                elif style == "italic":
                    slant = "italic"
                elif style == "underline":
                    underline = True
                elif style == "overstrike":
                    overstrike = True
                else:
                    raise ValueError("Unknown style %r" % style)

            return cls(
                family=family,
                size=size,
                weight=weight,
                slant=slant,
                underline=underline,
                overstrike=overstrike,
            )

        # If it was neither, just assume it's a font name.
        return cls(name=from_tcl(str, data))

    def to_tcl(self):
        return self.name
