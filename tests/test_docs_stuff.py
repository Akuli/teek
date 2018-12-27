import os

import pytest


DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')


@pytest.mark.slow
def test_manpage_url_checker(monkeypatch, capsys):
    monkeypatch.syspath_prepend(DOCS_DIR)
    import extensions

    asd_url = extensions.get_manpage_url('asd', 'tk')
    assert isinstance(asd_url, str)

    monkeypatch.setitem(os.environ, 'READTHEDOCS', 'True')
    assert capsys.readouterr() == ('', '')
    with pytest.raises(Exception):
        extensions.check_url(asd_url)

    output, errors = capsys.readouterr()
    assert 'extensions.py: checking if url exists' in output
    assert not errors
