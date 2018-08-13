import pkgutil
import subprocess
import sys

import examples


for junk, name, junk2 in pkgutil.iter_modules(examples.__path__, 'examples.'):
    if name != 'examples.__main__':
        if subprocess.call([sys.executable, '-m', name]) != 0:
            break
