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


def _anonymous_font_property(attribute):
    def fget(self):
        return self._description[attribute]

    return property(fget)


def _named_font_property(attribute):
    def fget(self):
        ty = self._OPTIONS_TYPE["-" + attribute]
        return tcl_call(ty, "font", "configure", self.name, "-" + attribute)

    def fset(self, value):
        tcl_call(None, "font", "configure", self.name, "-" + attribute, value)

    return property(fget, fset)


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
        description = {}

        if family is not None:
            description["family"] = family

        if size is not None:
            description["size"] = size

        if weight is not None:
            description["weight"] = weight

        if slant is not None:
            description["slant"] = slant

        if underline is not None:
            description["underline"] = underline

        if overstrike is not None:
            description["overstrike"] = overstrike

        self.name = None
        self._description = description

    family = _anonymous_font_property("family")
    size = _anonymous_font_property("size")
    weight = _anonymous_font_property("weight")
    slant = _anonymous_font_property("slant")
    underline = _anonymous_font_property("underline")
    overstrike = _anonymous_font_property("overstrike")

    def actual(self):
        if self.name is None:
            options = _dict2options(self._description)
            actual = tcl_call(self._OPTIONS_TYPE, "font", "actual", options)
        else:
            actual = tcl_call(self._OPTIONS_TYPE, "font", "actual", self.name)

        return _options2dict(actual)

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
            "family=%s, "
            "size=%s, "
            "weight=%s, "
            "slant=%s, "
            "underline=%s, "
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
        options = from_tcl(cls._OPTIONS_TYPE, "font", "actual", data)
        return cls(**_options2dict(options))

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

    family = _named_font_property("family")
    size = _named_font_property("size")
    weight = _named_font_property("weight")
    slant = _named_font_property("slant")
    underline = _named_font_property("underline")
    overstrike = _named_font_property("overstrike")

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
