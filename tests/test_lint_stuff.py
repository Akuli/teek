import os

import teek


# a comment like "fla ke8: noqa" without the space ignores the whole file
# usually that's not intended, except in __init__.py files
# a comment like "# noqa" only ignores the current line, that's good
def test_flake8_ignore_comments_are_of_correct_kind():
    for root, dirs, files in os.walk(teek.__path__[0]):
        # yes, this trick is documented
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for filename in files:
            if filename == '__init__.py' or not filename.endswith('.py'):
                continue

            with open(os.path.join(root, filename), encoding='utf-8') as file:
                for lineno, line in enumerate(file, start=1):
                    bad = '# fla' + 'ke8: no' + 'qa'
                    assert bad not in line, (filename, lineno)
