import os
import teek


EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'examples')


# magic ftw
# TODO: this doesn't work with pytest-xdist and pythons that don't have
#       ordered dict, i have no idea why and i don't know how to fix it
def _create_test_function(filename):
    with open(os.path.join(EXAMPLES_DIR, filename), 'r') as file:
        code = file.read()

    def func(monkeypatch, handy_callback):
        @handy_callback
        def fake_run():
            pass

        with monkeypatch.context() as monkey:
            monkey.setattr(teek, 'run', fake_run)
            exec(code, {'__file__': os.path.join(EXAMPLES_DIR, filename)})

        assert fake_run.ran_once()

        # make sure that nothing breaks if the real .run() is called
        teek.update()
        teek.after_idle(teek.quit)
        teek.run()

    func.__name__ = func.__qualname__ = 'test_' + filename.replace('.', '_')
    globals()[func.__name__] = func


for filename in sorted(os.listdir(EXAMPLES_DIR)):
    if filename.endswith('.py') and not filename.startswith('_'):
        _create_test_function(filename)
