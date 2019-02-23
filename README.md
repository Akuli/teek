# Teek

[![Build Status](https://travis-ci.org/Akuli/teek.svg?branch=master)](https://travis-ci.org/Akuli/teek)
[![Documentation Status](https://readthedocs.org/projects/teek/badge/?version=latest)](https://teek.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/Akuli/teek/badge.svg?branch=master)](https://coveralls.io/github/Akuli/teek?branch=master)

Teek is a pythonic and user-friendly alternative to tkinter. It doesn't come
with Python so you need to install it yourself, but it's nice and light-weight.

Documentation: https://teek.rtfd.org/


## Teek is Pythonic

If you have worked with tkinter a lot, you know that it's kind of annoying.
Almost everything is represented as strings in Tcl. Tkinter is dumb and it
doesn't try to do things like they would be usually done in Python; instead,
tkinter users need to deal with many inconveniences themselves. On the other
hand, Teek is *pythonic*; it does things like they are best done in Python,
not how they are done in Tcl.


### Ttk

Never heard of Ttk before? Shame on you. Ttk is the new way to write GUIs in
Tk, and you should be already using it in tkinter. Ttk GUIs look a *lot* better
than non-Ttk GUIs on most platforms. For example, this GUI has a Ttk button and
a non-Ttk button. Guess which is which:

[comment]: # (this must be a full url to make it work in pypi description)

![good and bad button](https://github.com/Akuli/teek/raw/master/tk-ttk.png)

The problem is that Tk's windows (in tkinter, `tkinter.Toplevel` and
`tkinter.Tk`) are *not* Ttk widgets. If you add Ttk widgets into them, the GUI
looks messy on some systems, like my linux system with MATE desktop. The
solution is to add a big Ttk frame that fills the window, and then add all
widgets into that frame.

**Tkinter:**

```python3
# this is a well-done hello world, and tbh, most people don't use tkinter "well"
import tkinter
from tkinter import ttk

root = tkinter.Tk()
big_frame = ttk.Frame(root)
big_frame.pack(fill='both', expand=True)   # make sure it fills the root window
ttk.Label(big_frame, text="Hello World!").pack()
root.mainloop()
```

**Teek:**

```python3
import teek

window = teek.Window("Hello")
teek.Label(window, "Hello World!").pack()
window.on_delete_window.connect(teek.quit)
teek.run()
```

All teek widgets are Ttk, so you don't need to do a separate import to use
ttk widgets. Also, when you create a teek `Window`, the big ttk frame is
created and packed automatically for you, and you don't need to think about it
at all; you just create a `Window` and add stuff into it.


### Threads

Here `time.sleep`s represent blocking things. In real life you could e.g. do
network requests, run a subprocess or perform CPU-sensitive computations in the
thread.

**Tkinter:**

```python3
import queue
import threading
import time
import tkinter

root = tkinter.Tk()
root.title("Thread Demo")
text = tkinter.Text(root)
text.pack()

message_queue = queue.Queue()

def queue_poller():
    while True:
        try:
            message = message_queue.get(block=False)
        except queue.Empty:
            break
        text.insert('end', message)

    root.after(50, queue_poller)

def thread_target():
    message_queue.put('doing things...\n')
    time.sleep(1)
    message_queue.put('doing more things...\n')
    time.sleep(2)
    message_queue.put('done')

threading.Thread(target=thread_target).start()
queue_poller()
root.mainloop()
```

**Teek:**

```python3
import threading
import time
import teek

text = teek.Text(teek.Window("Thread Demo"))
text.pack()

def thread_target():
    text.insert(text.end, 'doing things...\n')
    time.sleep(1)
    text.insert(text.end, 'doing more things...\n')
    time.sleep(2)
    text.insert(text.end, 'done')

teek.init_threads()
threading.Thread(target=thread_target).start()
window.on_delete_window.connect(teek.quit)
teek.run()
```

This is not a joke. Using threads with tkinter is a horrible mess, but teek
works with threads nicely. All you need is `teek.init_threads()`, and then you
can do teek things from threads. See [concurrency docs] for details.

[concurrency docs]: https://teek.readthedocs.io/en/latest/concurrency.html


### Debuggability

**Tkinter:**

```python3
label = ttk.Label(some_widget, text="hello world")
print(label)        # prints something like '.140269016152776', which is confusing
print(repr(label))  # somewhat better: <tkinter.ttk.Label object .140269016152776>
```

**Teek:**

```python3
label = teek.Label(some_widget, "hello world")
print(label)    # <teek.Label widget: text='hello world'>
```


### Text Widget Indexes

The 4th character of the 3rd line of a text widget is the string `'3.4'` in
Tcl and tkinter. This is not only confusing because `3.4` looks like a float
even though treating it as a float messes things up, but this makes code look
messy.

**Tkinter:**

```python3
# figure out where the cursor is
line, column = textwidget.index('insert').split('.')
line = int(line)
column = int(column)

# same thing, more concise
line, column = map(int, textwidget.index('insert').split('.'))
```

**Teek:**

```python3
line, column = textwidget.marks['insert']
```

`textwidget.marks` is a dictionary-like object with mark names as keys and text
index namedtuples as values. Teek represents text indexes as namedtuples
that have `line` and `column` attributes, which is useful if you only need the
line. In tkinter, you need to parse the `'line.column'` string with
`.split('.')` and take the first element of the split result.

**Tkinter:**

```python3
cursor_lineno = int(textwidget.index('insert').split('.')[0])
```

**Teek:**

```python3
cursor_lineno = textwidget.marks['insert'].line
```

In tkinter you also need to construct the `'line.column'` strings yourself, but
in teek you can use `(line, column)` tuples.

**Tkinter:**

```python3
textwidget.mark_set('insert', '{}.{}'.format(new_cursor_line, new_cursor_column))
```

**Teek:**

```python3
textwidget.marks['insert'] = (new_cursor_line, new_cursor_column)
```

Tcl uses strings like `3.4 + 5 chars` to denote the position that is 5
characters after the position `3.4`. Teek's text position namedtuples have a
pythonic `forward()` method that returns a new text position.

**Tkinter:**

```python3
# textwidget.index always returns the position as 'line.column'
new_position = textwidget.index('{}.{} + 5 chars - 1 line'.format(line, column))
# now new_position is a string, and you may need to parse it back to
# separate line and column
```

**Teek:**

```python3
new_position = textwidget.index(line, column).forward(chars=5).back(lines=1)
# new_position is now a text position namedtuple
```


### Timeouts

In tkinter, `any_widget.after(1000, func)` runs `func()` after 1 second, and
the `any_widget` can be any tkinter widget. That's right, you need a widget for
scheduling timeouts. This can be a problem in library code. But what if during
that 1 second of waiting time, you decide that you don't want to run the
timeout after all? You can cancel the timeout, but as usual, teek makes it
easier.

**Tkinter:**

```python3
widget = get_some_widget_from_somewhere()
timeout_id = widget.after(1000, my_function)
...
# debugging
print(timeout_id)       # prints 'after#0'... very useful, eh??
...
if we_actually_dont_want_to_timeout():
    widget.after_cancel(timeout_id)
    print(timeout_id)   # still prints 'after#0'
```

**Teek:**

```python3
timeout_object = teek.after(1000, my_function)
...
# debugging
print(timeout_object)   # prints <pending 'my_function' timeout 'after#0'>
...
if we_actually_dont_want_to_timeout():
    timeout.cancel()
    print(timeout)      # prints <cancelled 'my_function' timeout 'after#0'>
```


## Developing teek

This section contains the commands I use when working on teek. If you
use windows, replace `python3` with `py`.

- `python3 -m pip install --user sphinx pytest pytest-cov flit` installs
  everything you need for developing teek.
- `python3 -m pytest` runs tests (they are in the `tests` subdirectory). It is
  normal to get lots of tiny windows on the screen while running the tests. I
  use these pytest options:
    - `--skipslow` makes the tests run faster by skipping tests that are
      decorated with `@pytest.mark.slow`.
    - `--durations=10` prints the list of 10 slowest tests at the end of the
      test run. This is a good way to figure out which tests to mark slow.
    - `--cov=teek` runs the tests under coverage. Run
      `python3 -m coverage html` and open `htmlcov/index.html` to view the
      results. Coverage results from travis builds go to [coveralls].
- `cd docs` followed by `py -m sphinx . _build` builds documentation locally.
  You can view it by opening `docs/_build/index.html` in your browser.
  [readthedocs builds the docs] when you push to master, but it's best to make
  sure that everything's fine first.
- Sphinx seems to only build parts of the documentation if you change some of
  it, but sometimes it doesn't detect your changes. Run `cd docs` followed by
  `rm -r _build` to make it build everything next time.
- I don't usually lint the files on my system. I push to GitHub (to any
  branch), and if [the travis build] fails, I know I did something badly. If
  you want to lint things yourself, find the correct command from
  `.travis.yml`.
- `flit publish` uploads to PyPI. You can ask me to run this after I have
  merged something to master.

[readthedocs builds the docs]: https://readthedocs.org/projects/teek/builds/
[the travis build]: https://travis-ci.org/Akuli/teek
[coveralls]: https://coveralls.io/github/Akuli/teek
