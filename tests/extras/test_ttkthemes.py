import pytest

import teek
from teek.extras import ttkthemes


@pytest.mark.slow
@pytest.mark.skipif(ttkthemes.ttkthemes4tkinter is None,
                    reason="ttkthemes is not installed")
def test_theme_setting_getting_listing(monkeypatch):
    # these widgets should get themed in many ways during the test
    window = teek.Window()
    teek.Label(window, "hello world").pack()
    teek.Button(window, "I'm a button!!", (lambda: print('click'))).pack()

    def do_checks():
        manager = ttkthemes.ThemeManager()
        assert isinstance(manager.get_themes(), list)
        assert manager.get_themes()

        # sorting is mostly for debuggability
        for theme in sorted(manager.get_themes()):
            assert manager.current_theme != theme
            manager.current_theme = theme
            assert manager.current_theme == theme
            teek.update()

    if ttkthemes.ttkthemes4tkinter is not None:
        do_checks()

    # test what happens if ttkthemes can't be imported
    teek.after_idle(teek.quit)
    teek.run()
    monkeypatch.setattr(ttkthemes, 'ttkthemes4tkinter', None)
    do_checks()
