import os
import pythotk


EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'examples')


# magic ftw
def _create_test_function(filename):
    with open(os.path.join(EXAMPLES_DIR, filename), 'r') as file:
        code = file.read()

    def func(monkeypatch):
        with monkeypatch.context() as monkey:
            monkey.setattr(pythotk, 'run', (lambda: None))
            exec(code, {'__file__': os.path.join(EXAMPLES_DIR, filename)})

        # make sure that nothing breaks if the real .run() is called
        pythotk.update()
        pythotk.after_idle(pythotk.quit)
        pythotk.run()

    func.__name__ = func.__qualname__ = 'test_' + filename.replace('.', '_')
    globals()[func.__name__] = func


for filename in os.listdir(EXAMPLES_DIR):
    if filename.endswith('.py') and not filename.startswith('_'):
        _create_test_function(filename)
