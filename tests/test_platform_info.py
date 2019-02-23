import pytest

import teek


def test_versions():
    for version in [teek.TCL_VERSION, teek.TK_VERSION]:
        assert isinstance(version, tuple)
        major, minor = version
        assert isinstance(major, int)
        assert isinstance(minor, int)


def test_version_check(monkeypatch):
    with pytest.raises(AttributeError):
        teek.version_check

    from teek import _platform_info
    monkeypatch.setattr(_platform_info, 'TCL_VERSION', (1, 2))
    monkeypatch.setattr(_platform_info, 'TK_VERSION', (3, 4))

    with pytest.raises(RuntimeError) as error:
        _platform_info._version_check()
    assert str(error.value) == (
        "sorry, your Tcl/Tk installation is too old "
        "(expected 8.5 or newer, found Tcl 1.2 and Tk 3.4)")


def test_windowingsystem():
    assert teek.windowingsystem() in {'x11', 'aqua', 'win32'}
