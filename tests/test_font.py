import pytest

import pythotk as tk
import pythotk.font as tkfont       # TODO: i dislike this


def test_font_magic_new_method():
    font = tkfont.Font('a_font_with_this_name_does_not_exist')
    assert isinstance(font, tkfont.Font)
    assert not isinstance(font, tkfont.NamedFont)

    tk.eval(None, 'font create test_font_name')
    named_font = tkfont.Font('test_font_name')
    assert isinstance(named_font, tkfont.NamedFont)
    named_font.delete()


def test_repr_eq_hash():
    font = tkfont.Font(('Helvetica', 12))
    named_font = tkfont.NamedFont('asda')
    assert repr(font) == "Font(('Helvetica', 12))"
    assert repr(named_font) == "NamedFont('asda')"

    another_named_font = tkfont.NamedFont('asda')
    assert named_font == another_named_font
    assert {named_font: 'toot'}[another_named_font] == 'toot'

    def all_names():
        return (font.to_tcl()
                for font in tkfont.NamedFont.get_all_named_fonts())

    assert 'asda' in all_names()
    named_font.delete()
    assert 'asda' not in all_names()

    assert font != 'toot'
    assert named_font != 'toot'


def test_from_to_tcl():
    description = ["Helvetica", 42, "bold"]
    descriptiony_font = tkfont.Font(description)
    assert descriptiony_font.to_tcl() is description
    assert tkfont.Font.from_tcl(description) == descriptiony_font

    tk.eval(None, 'font create test_font_name')
    named_font = tkfont.NamedFont.from_tcl('test_font_name')
    assert isinstance(named_font, tkfont.NamedFont)
    assert named_font.to_tcl() == 'test_font_name'
    named_font.delete()


def test_properties():
    anonymous_font = tkfont.Font(("Helvetica", 42, "bold", "underline"))
    named_font = tkfont.NamedFont(
        family='Helvetica', size=42, weight='bold', underline=True)

    # just to make debugging easier because these facts are needed below
    assert not isinstance(anonymous_font, tkfont.NamedFont)
    assert isinstance(named_font, tkfont.NamedFont)

    for font in [anonymous_font, named_font]:
        assert font.size == 42
        assert font.weight == "bold"
        assert font.slant == "roman"
        assert font.underline is True
        assert font.overstrike is False

        # the actual properties might differ from the font specification, e.g.
        # "Helvetica" is "Nimbus Sans L" on my system
        assert isinstance(font.family, str)

    # test setting error
    with pytest.raises(AttributeError) as error:
        anonymous_font.weight = "normal"
    assert '.to_named_font()' in str(error.value)

    # test successful setting
    assert named_font.underline is True
    named_font.underline = False
    assert named_font.underline is False

    assert not hasattr(anonymous_font, 'delete')
    named_font.delete()


def test_measure():
    assert tkfont.Font(('Helvetica', 42, 'bold')).measure('') == 0


def test_metrics():
    metrics = tkfont.Font(('Helvetica', 42, 'bold')).metrics()
    assert isinstance(metrics['ascent'], int)
    assert isinstance(metrics['descent'], int)
    assert isinstance(metrics['linespace'], int)
    assert isinstance(metrics['fixed'], bool)


def test_families():
    families = tkfont.Font.families()
    assert isinstance(families, list)
    assert families
    for family in families:
        assert isinstance(family, str)
        assert not family.startswith('@')


def fonts_are_similar(font1, font2):
    return (font1.family == font2.family and
            font1.size == font2.size and
            font1.weight == font2.weight and
            font1.slant == font2.slant and
            font1.underline is font2.underline and
            font1.overstrike is font2.overstrike)


def test_to_named_font():
    anonymous = tkfont.Font(('Helvetica', 42))
    named = anonymous.to_named_font()
    assert isinstance(named, tkfont.NamedFont)
    assert fonts_are_similar(anonymous, named)

    named2 = named.to_named_font()      # creates a copy
    assert isinstance(named2, tkfont.NamedFont)
    assert named != named2      # it is a copy
    assert fonts_are_similar(named, named2)

    named2.weight = 'bold'
    assert named.weight != named2.weight
    named2.weight = 'normal'
    assert fonts_are_similar(named, named2)

    named.delete()
    named2.delete()
