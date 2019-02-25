import io

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
    return teek.Image(data=file.read())


def from_bytes(bytes_):
    return teek.Image(data=bytes_)
