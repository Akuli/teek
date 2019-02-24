import os
import random
import tempfile

import pytest

import teek


SMILEY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'smiley.gif')


def test_width_and_height():
    image = teek.Image(file=SMILEY_PATH)
    assert image.width == 32
    assert image.height == 32


# tests that use this so that it returns True (for loops run) are marked slow
def slow_content_eq_check(image1, image2):
    # magic ftw, the double for loop is slow with big images which is why the
    # test images are small
    return (
        image1.width == image2.width and
        image1.height == image2.height and
        all(
            image1.get(x, y) == image2.get(x, y)
            for x in range(image1.width)
            for y in range(image1.height)
        )
    )


@pytest.mark.slow
def test_images_contain_same_data_util():
    image1 = teek.Image(file=SMILEY_PATH)
    image2 = teek.Image(file=SMILEY_PATH)
    assert slow_content_eq_check(image1, image1)
    assert slow_content_eq_check(image1, image2)

    image3 = teek.Image(width=1, height=2)
    assert not slow_content_eq_check(image1, image3)


def test_config(check_config_types):
    check_config_types(teek.Image(file=SMILEY_PATH).config, 'Image')


@pytest.mark.slow
def test_data_base64():
    with open(SMILEY_PATH, 'rb') as file:
        binary_data = file.read()

    assert slow_content_eq_check(teek.Image(file=SMILEY_PATH),
                                 teek.Image(data=binary_data))


@pytest.mark.slow
def test_from_to_tcl():
    image1 = teek.Image(file=SMILEY_PATH)
    teek.tcl_eval(None, 'proc returnArg {arg} {return $arg}')
    image2 = teek.tcl_call(teek.Image, 'returnArg', image1)
    assert image1.to_tcl() == image2.to_tcl()   # no implicit copying
    assert image1 is not image2                 # no implicit cache
    assert slow_content_eq_check(image1, image2)


def test_eq_hash():
    image1 = teek.Image(file=SMILEY_PATH)
    image2 = teek.Image.from_tcl(image1.to_tcl())
    image3 = teek.Image(file=SMILEY_PATH)

    assert image1 == image2
    assert {image1: 'woot'}[image2] == 'woot'
    assert image1 != image3
    assert image2 != image3
    assert image2 != 'woot'


def test_delete_and_all_images():
    old_images = set(teek.Image.get_all_images())
    new_image = teek.Image()
    assert set(teek.Image.get_all_images()) == old_images | {new_image}
    new_image.delete()
    assert set(teek.Image.get_all_images()) == old_images


def test_repr():
    image = teek.Image(file=SMILEY_PATH)
    assert repr(image) == '<Image: from %s, 32x32>' % repr(SMILEY_PATH)
    image.delete()
    assert repr(image) == '<Image: from %s, deleted>' % repr(SMILEY_PATH)

    image2 = teek.Image(width=123, height=456)
    assert repr(image2) == '<Image: 123x456>'
    image2.delete()
    assert repr(image2) == '<Image: deleted>'


def test_in_use():
    image = teek.Image(file=SMILEY_PATH)
    assert image.in_use() is False
    window = teek.Window()
    assert image.in_use() is False

    widget = teek.Label(window, image=image)
    assert image.in_use() is True
    widget2 = teek.Label(window, image=image)
    assert image.in_use() is True
    widget.destroy()
    assert image.in_use() is True
    widget2.destroy()
    assert image.in_use() is False


def test_blank():
    image1 = teek.Image(file=SMILEY_PATH)
    image2 = image1.copy()
    image2.blank()
    assert not slow_content_eq_check(image1, image2)      # not slow


@pytest.mark.slow
def test_read():
    image1 = teek.Image(file=SMILEY_PATH)
    assert image1.width > 0 and image1.height > 0

    image2 = teek.Image()
    assert image2.width == image2.height == 0
    image2.read(SMILEY_PATH)
    assert (image2.width, image2.height) == (image1.width, image1.height)
    assert slow_content_eq_check(image1, image2)


def test_redither():
    # no idea what this should do, so let's test that it does something...
    # except that it doesn't seem to actually do anything to the smiley, so
    # just test that it calls the Tcl redither command
    called = []
    fake_image = teek.create_command(called.append, [str])
    teek.Image.from_tcl(fake_image).redither()
    assert called == ['redither']


def test_transparency():
    image = teek.Image(file=SMILEY_PATH)
    x = random.randint(0, image.width - 1)
    y = random.randint(0, image.height - 1)
    assert image.transparency_get(x, y) is False
    image.transparency_set(x, y, True)
    assert image.transparency_get(x, y) is True
    image.transparency_set(x, y, False)
    assert image.transparency_get(x, y) is False


@pytest.mark.slow
def test_write():
    image1 = teek.Image(file=SMILEY_PATH)
    with tempfile.TemporaryDirectory() as tmpdir:
        asd = os.path.join(tmpdir, 'asd.gif')
        image1.write(asd, format='gif')
        image2 = teek.Image(file=asd)
    assert slow_content_eq_check(image1, image2)


def test_get_bytes():
    image = teek.Image(file=SMILEY_PATH)

    with tempfile.TemporaryDirectory() as tmpdir:
        asd = os.path.join(tmpdir, 'asd.gif')
        image.write(asd, format='gif')
        with open(asd, 'rb') as file:
            actual_gif_bytes = file.read()

    assert image.get_bytes('gif') == actual_gif_bytes
