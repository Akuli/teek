from ._tcl_calls import call as tcl_call, to_tcl, from_tcl
from . import TclError


def _dict2options(dict_):
    tcl_options = []
    for k, v in dict_.items():
        tcl_options.append("-" + k)
        tcl_options.append(to_tcl(v))
    return tcl_options


def _options2dict(options):
    return {k.lstrip("-"): v for k, v in options.items()}


def _font_property(attribute):
    def getter(self):
        if self.name is None:
            return self._description[attribute]
        else:
            ty = self._OPTIONS_TYPE["-" + attribute]
            return tcl_call(
                ty, "font", "configure", self.name, "-" + attribute
            )

    def setter(self, value):
        if self.name is None:
            self._description[attribute] = value
        else:
            tcl_call(
                None, "font", "configure", self.name, "-" + attribute, value
            )

    return property(getter, setter)


class AnonymousFont:
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

        self.name = None
        self._description = options

    family = _font_property("family")
    size = _font_property("size")
    weight = _font_property("weight")
    slant = _font_property("slant")
    underline = _font_property("underline")
    overstrike = _font_property("overstrike")

    def actual(self):
        if self.name is None:
            options = tcl_call(
                self._OPTIONS_TYPE,
                "font",
                "actual",
                _dict2options(self._description),
            )
        else:
            options = tcl_call(self._OPTIONS_TYPE, "font", "actual", self.name)

        return _options2dict(options)

    def delete(self):
        if self.name is None:
            raise RuntimeError("Can't delete an AnonymousFont!")

        tcl_call(None, "font", "delete", self.name)

    def measure(self, text):
        if self.name is None:
            return tcl_call(
                int, "font", "measure", _dict2options(self._description), text
            )
        else:
            return tcl_call(int, "font", "measure", self.name, text)

    def metrics(self):
        ty = {"ascent": int, "descent": int, "linespace": int, "fixed": bool}
        if self.name is None:
            return tcl_call(ty, "font", "metrics", self.name)
        else:
            return tcl_call(
                ty, "font", "metrics", _dict2options(self._description)
            )

    @classmethod
    def families(self):
        return tcl_call([str], "font", "families")

    def __repr__(self):
        return (
            "%s("
            "family=%s,"
            "size=%s,"
            "weight=%s,"
            "slant=%s,"
            "underline=%s,"
            "overstrike=%s"
            ")"
        ) % (
            self.__class__.__name__,
            self.family,
            self.size,
            self.weight,
            self.slant,
            self.underline,
            self.overstrike,
        )

    def __eq__(self, other):
        return self._description == other._description

    @classmethod
    def from_tcl(cls, data):
        # Check if this is a font description in the form of an options list.
        try:
            options = from_tcl(cls._OPTIONS_TYPE, data)
            assert not (options.keys() - cls._OPTIONS_TYPE.keys())
        except (TclError, ValueError, AssertionError):
            pass
        else:
            return cls(**_options2dict(options))

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
                size=int(size),
                weight=weight,
                slant=slant,
                underline=underline,
                overstrike=overstrike,
            )

        raise ValueError(
            "Don't know how to get a %s from %r" % (cls.__name__, data)
        )

    def to_tcl(self):
        return _dict2options(self._description)


class NamedFont(AnonymousFont):
    def __init__(self, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if name is None:
            options = _dict2options(self._description)
            self.name = tcl_call(str, "font", "create", *options)
        else:
            self.name = name
            options = _dict2options(self._description)
            try:
                tcl_call(str, "font", "create", name, *options)
            except TclError:
                # font already exists
                pass

    @classmethod
    def names(self):
        return tcl_call([str], "font", "names")

    @classmethod
    def from_tcl(cls, data):
        if data in cls.names():
            return cls(data)
        else:
            return super().from_tcl(data)

    def to_tcl(self):
        return self.name

    def __repr__(self):
        return ("%s(name=%s)") % (self.__class__.__name__, self.name)

    def __eq__(self, other):
        return self.name == other.name
