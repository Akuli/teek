import io
import os
import sys

import pytest

import teek
try:
    from teek.extras import image_loader
except ImportError as e:
    assert 'pip install teek[image_loader]' in str(e)
    image_loader = None
else:
    import PIL.Image


ignore_svglib_warnings = pytest.mark.filterwarnings(
    "ignore:The 'warn' method is deprecated")
needs_image_loader = pytest.mark.skipif(
    image_loader is None,
    reason="teek.extras.image_loader dependencies are not installed")

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def test_nice_import_error(monkeypatch, tmp_path):
    old_modules = sys.modules.copy()
    try:
        for module in ['PIL', 'PIL.Image', 'teek.extras.image_loader']:
            if module in sys.modules:
                del sys.modules[module]

        with open(os.path.join(str(tmp_path), 'PIL.py'), 'w') as bad_pil:
            bad_pil.write('raise ImportError("oh no")')

        monkeypatch.syspath_prepend(str(tmp_path))
        with pytest.raises(ImportError) as error:
            import teek.extras.image_loader     # noqa

        assert str(error.value) == (
            "oh no. Maybe try 'pip install teek[image_loader]' to fix this?")
    finally:
        sys.modules.update(old_modules)


def images_equal(image1, image2):
    if image1.width != image2.width or image1.height != image2.height:
        return False
    return image1.get_bytes('gif') == image2.get_bytes('gif')


@needs_image_loader
@pytest.mark.filterwarnings("ignore:unclosed file")     # because PIL
def test_from_pil():
    smiley1 = teek.Image(file=os.path.join(DATA_DIR, 'smiley.gif'))
    with PIL.Image.open(os.path.join(DATA_DIR, 'smiley.gif')) as pillu:
        smiley2 = image_loader.from_pil(pillu)
    assert images_equal(smiley1, smiley2)


# yields different kinds of file objects that contain the data from the file
def open_file(path):
    with open(path, 'rb') as file:
        yield file
        file.seek(0)
        yield io.BytesIO(file.read())


@needs_image_loader
def test_from_file_gif():
    smiley1 = teek.Image(file=os.path.join(DATA_DIR, 'smiley.gif'))
    for file in open_file(os.path.join(DATA_DIR, 'smiley.gif')):
        smiley2 = image_loader.from_file(file)
        assert images_equal(smiley1, smiley2)


@needs_image_loader
def test_from_file_pil():
    smileys = []
    for file in open_file(os.path.join(DATA_DIR, 'smiley.jpg')):
        smileys.append(image_loader.from_file(file))

    for smiley in smileys:
        assert smiley.width == 32
        assert smiley.height == 32
        assert images_equal(smiley, smileys[0])


@needs_image_loader
@ignore_svglib_warnings
def test_from_file_svg():
    firefoxes = []
    for file in open_file(os.path.join(DATA_DIR, 'firefox.svg')):
        firefoxes.append(image_loader.from_file(file))

    for firefox in firefoxes:
        assert firefox.width == 1024
        assert firefox.height == 1024
        assert images_equal(firefox, firefoxes[0])


@needs_image_loader
@ignore_svglib_warnings
def test_from_bytes():
    with open(os.path.join(DATA_DIR, 'firefox.svg'), 'rb') as file:
        fire = image_loader.from_file(file)
        file.seek(0)
        fox = image_loader.from_bytes(file.read())

    assert images_equal(fire, fox)
