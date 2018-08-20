from pythotk.font import Font


def test_properties():
    NAME = "name_test"

    font = Font(
        name=NAME,
        family="Helvetica",
        weight="bold",
        overstrike=True,
        underline=False,
        size=42,
        slant="roman",
    )

    assert font.name == NAME
    assert font.family == "Helvetica"
    assert font.weight == "bold"
    assert font.overstrike is True
    assert font.underline is False
    assert font.size == 42
    assert font.slant == "roman"

    font.weight = "normal"
    assert font.weight == "normal"


def test_deletion():
    NAME = "deletion_test"

    font = Font(name=NAME)

    assert NAME in Font.names()
    font.delete()
    assert NAME not in Font.names()


def test_actual_is_valid_init_args():
    PRIME_NAME = "actual_init_args_test_prime"
    CLONE_NAME = "actual_init_args_test_clone"

    prime_font = Font(
        name=PRIME_NAME, family="Helvetica", weight="bold", overstrike=True
    )
    clone_font = Font(name=CLONE_NAME, **prime_font.actual())

    assert prime_font.name == PRIME_NAME
    assert clone_font.name == CLONE_NAME

    assert clone_font.actual() == clone_font._options
    assert prime_font.actual() == clone_font._options


def test_double_creation():
    NAME = "double_creation_test"

    font_x = Font(
        name=NAME,
        family="Calibri",
        weight="bold",
        slant="italic",
        size=37,
        overstrike=True,
        underline=True,
    )
    font_y = Font(name=NAME)

    assert font_x is not font_y
    assert font_x.name == font_y.name
    assert font_x._options == font_y._options


def test_internal_get_options_for_name():
    NAME = "internal_get_options_for_name_test"

    font = Font(
        name=NAME,
        family="Helvetica",
        weight="bold",
        overstrike=True,
        underline=False,
        size=42,
        slant="roman",
    )

    assert font._options == Font._get_options_for_name(NAME)


def test_options_is_valid_init_args():
    PRIME_NAME = "options_init_args_test_prime"
    CLONE_NAME = "options_init_args_test_clone"

    prime_font = Font(
        name=PRIME_NAME, family="Helvetica", weight="bold", overstrike=True
    )
    clone_font = Font(name=CLONE_NAME, **prime_font._options)

    assert prime_font.name != clone_font.name
    assert prime_font._options == clone_font._options
    assert prime_font.actual() == clone_font.actual()
