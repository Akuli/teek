from pythotk._tcl_calls import call as tcl_call, to_tcl

# Font man page:
# https://www.tcl.tk/man/tcl8.5/TkCmd/font.html


def _tcl_options(py_options):
    tcl_options = []
    for k, v in py_options.items():
        tcl_options.append("-" + k)
        tcl_options.append(to_tcl(v))
    return tcl_options

def _font_configure_property(name):
    def getter(self):
        return self._options[name]

    def setter(self, value):
        self._options[name] = value
        tcl_call(None, "font", "configure", name, value)

    return property(getter, setter)


class Font:
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

        options = _tcl_options(options)

        if name is None:
            name = tcl_call(str, "font", "create", *options)
        else:
            tcl_call(None, "font", "create", name, *options)

        self.name = name
        self._options = {
            "family": family,
            "size": size,
            "weight": weight,
            "slant": slant,
            "underline": underline,
            "overstrike": overstrike,
        }

        # TODO: Call 'font actual' on the font.

    family = _font_configure_property("family")
    size = _font_configure_property("size")
    weight = _font_configure_property("weight")
    slant = _font_configure_property("slant")
    underline = _font_configure_property("underline")
    overstrike = _font_configure_property("overstrike")

    def delete(self):
        tcl_call(None, "font", "delete", self.name)

    def measure(self, text):
        return tcl_call(int, "font", "measure", self.name, text)

    def metrics(self, option=None, ty=str):
        if option is None:
            return tcl_call(ty, "font", "metrics")
        else:
            return tcl_call(ty, "font", "metrics", option)

    @classmethod
    def families(self):
        return tcl_call([str], "font", "families")

    @classmethod
    def names(self):
        return tcl_call([str], "font", "names")
