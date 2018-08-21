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

    assert clone_font.actual() == prime_font.actual()


def test_existing_name():
    NAME = "existing_name_test"

    font_x = Font(
        name=NAME,
        family="Courier",
        weight="bold",
        slant="italic",
        size=37,
        overstrike=True,
        underline=True,
    )
    font_y = Font(name=NAME)

    assert font_x is not font_y
    assert font_x == font_y


def test_to_tcl():
    NAME = "to_tcl_test"

    font = Font(
        name=NAME,
        family="Calibri",
        weight="bold",
        slant="italic",
        size=37,
        overstrike=True,
        underline=True,
    )

    assert font.to_tcl() == font.name


def test_from_tcl():
    font = Font(
        name="from_tcl_test",
        family="Calibri",
        weight="bold",
        slant="italic",
        size=37,
        overstrike=True,
        underline=True,
    )
    assert Font.from_tcl(font.name) == font

    font = Font.from_tcl("Helvetica 7 bold underline")
    assert font.family == "Helvetica"
    assert font.size == 7
    assert font.weight == "bold"
    assert font.underline is True

    font = Font.from_tcl("-family Times -size 3 -overstrike 1")
    assert font.family == "Times"
    assert font.size == 3
    assert font.overstrike is True
