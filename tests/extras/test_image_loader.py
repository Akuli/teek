import io
import os
import sys

import pytest

import teek
from teek.extras import image_loader_dummy
try:
    from teek.extras import image_loader
    loader_libs = [image_loader, image_loader_dummy]
except ImportError as e:
    assert 'pip install teek[image_loader]' in str(e)
    image_loader = None
    loader_libs = [image_loader_dummy]
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
    for lib in loader_libs:
        smiley1 = teek.Image(file=os.path.join(DATA_DIR, 'smiley.gif'))
        with PIL.Image.open(os.path.join(DATA_DIR, 'smiley.gif')) as pillu:
            smiley2 = lib.from_pil(pillu)
        assert images_equal(smiley1, smiley2)


# yields different kinds of file objects that contain the data from the file
def open_file(path):
    with open(path, 'rb') as file:
        yield io.BytesIO(file.read())
        file.seek(0)
        yield file


def test_from_file_gif():
    for lib in loader_libs:
        smiley1 = teek.Image(file=os.path.join(DATA_DIR, 'smiley.gif'))
        for file in open_file(os.path.join(DATA_DIR, 'smiley.gif')):
            smiley2 = lib.from_file(file)
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
@pytest.mark.slow
def test_from_file_svg():
    for filename in ['firefox.svg', 'rectangle.svg']:
        images = []
        for file in open_file(os.path.join(DATA_DIR, filename)):
            images.append(image_loader.from_file(file))

        for image in images:
            assert images_equal(image, images[0])


def test_from_bytes():
    for lib in loader_libs:
        with open(os.path.join(DATA_DIR, 'smiley.gif'), 'rb') as file1:
            smiley1 = lib.from_file(file1)
        with open(os.path.join(DATA_DIR, 'smiley.gif'), 'rb') as file2:
            smiley2 = lib.from_bytes(file2.read())
        assert images_equal(smiley1, smiley2)
