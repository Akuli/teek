import io
import shutil
import tempfile

# see pyproject.toml
try:
    import lxml.etree
    import PIL.Image
    import reportlab.graphics.renderPM
    from svglib import svglib
except ImportError as e:
    raise ImportError(str(e) + ". Maybe try 'pip install teek[image_loader]' "
                      "to fix this?").with_traceback(e.__traceback__) from None

import teek


def from_pil(pil_image, **kwargs):
    """Converts a PIL_ ``Image`` object to a :class:`teek.Image`.

    All keyword arguments are passed to PIL's save_ method.

    .. _PIL: https://pillow.readthedocs.io/en/stable/
    .. _save: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL\
.Image.Image.save
    """
    # TODO: borrow some magic code from PIL.ImageTk to make this faster?
    #       or maybe optimize teek.Image? currently it base64 encodes the data
    gif = io.BytesIO()
    pil_image.save(gif, 'gif', **kwargs)
    return teek.Image(data=gif.getvalue())


def from_file(file):
    """Creates a :class:`teek.Image` from a file object.

    The file object must be readable, and it must be in bytes mode. It must
    have ``read()``, ``seek()`` and ``tell()`` methods. For example, files from
    ``open(some_path, 'rb')`` and ``io.BytesIO(some_data)`` work.

    This supports all file formats that PIL supports and SVG.

    Example::

        from teek.extras import image_loader

        with open(the_image_path, 'rb') as file:
            image = image_loader.from_file(file)
    """
    first_3_bytes = file.read(3)
    file.seek(0)
    if first_3_bytes == b'GIF':
        return teek.Image(data=file.read())

    # https://stackoverflow.com/a/15136684
    try:
        event, element = next(lxml.etree.iterparse(file, ('start',)))
        is_svg = (element.tag == '{http://www.w3.org/2000/svg}svg')
    except (lxml.etree.ParseError, StopIteration):
        is_svg = False
    file.seek(0)

    if is_svg:
        # svglib takes open file objects, even though it doesn't look like it
        # https://github.com/deeplook/svglib/issues/173
        rlg = svglib.svg2rlg(io.TextIOWrapper(file, encoding='utf-8'))

        with reportlab.graphics.renderPM.drawToPIL(rlg) as pil_image:
            return from_pil(pil_image)

    with PIL.Image.open(file) as pil_image:
        return from_pil(pil_image)


def from_bytes(bytes_):
    """
    Creates a :class:`teek.Image` from bytes that would normally be in an image
    file.

    Example::

        # if you have a file, it's recommended to use
        # from_file() instead, but this example works anyway
        with open(the_image_path, 'rb') as file:
            data = file.read()

        image = image_loader.from_bytes(data)
    """
    with io.BytesIO(bytes_) as fake_file:
        return from_file(fake_file)
