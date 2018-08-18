# Pythotk

[![Build Status](https://travis-ci.org/Akuli/pythotk.svg?branch=master)](https://travis-ci.org/Akuli/pythotk)
[![Documentation Status](https://readthedocs.org/projects/pythotk/badge/?version=latest)](https://pythotk.readthedocs.io/en/latest/?badge=latest)

Pythotk, short for "pythonic Tk", is a pythonic and user-friendly alternative
to tkinter. It doesn't come with Python so you need to install it yourself, but
it's nice and light-weight.

Documentation: https://pythotk.rtfd.org/


## Pythotk is Pythonic

If you have worked with tkinter a lot, you know that it's kind of annoying.
Almost everything is represented as strings in Tcl. Tkinter is dumb and it
doesn't try to do things like they would be usually done in Python; instead,
tkinter users need to deal with many inconveniences themselves. On the other
hand, Pythotk is *pythonic*; it does things like they are best done in Python,
not how they are done in Tcl.


### Ttk

Never heard of Ttk before? Shame on you. Ttk is the new way to write GUIs in
Tk, and you should be already using it in tkinter. Ttk GUIs look a *lot* better
than non-Ttk GUIs on most platforms. For example, this GUI has a Ttk button and
a non-Ttk button. Guess which is which:

![good and bad button](tk-ttk.png)

The problem is that Tk's windows (in tkinter, `tkinter.Toplevel` and
`tkinter.Tk`) are *not* Ttk widgets. If you add Ttk widgets into them, the GUI
looks messy on some systems, like my linux system with MATE desktop. The
solution is to add a big Ttk frame that fills the window, and then add all
widgets into that frame.

**Tkinter:**

```python3
# this is a well-done hello world, and tbh, most people don't use tkinter "well"
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
big_frame = ttk.Frame(root)
big_frame.pack(fill='both', expand=True)   # make sure it fills the root window
ttk.Label(big_frame, text="Hello World!").pack()
root.mainloop()
```

**Pythotk:**

```python3
import pythotk as tk

window = tk.Window("Hello")
tk.Label(window, "Hello World!").pack()
window.on_delete_window.connect(tk.quit)
tk.run()
```

All pythotk widgets are Ttk, so you don't need to do a separate import to use
ttk widgets. Also, when you create a pythotk `Window`, the big ttk frame is
created and packed automatically for you, and you don't need to think about it
at all; you just create a `Window` and add stuff into it.


### Debuggability

**Tkinter:**

```python3
label = ttk.Label(some_widget, text="hello world")
print(label)        # prints something like '.140269016152776', which is confusing
print(repr(label))  # somewhat better: <tkinter.ttk.Label object .140269016152776>
```

**Pythotk:**

```python3
label = tk.Label(some_widget, "hello world")
print(label)    # <pythotk.Label widget: text='hello world'>
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

**Pythotk:**

```python3
line, column = textwidget.marks['insert']
```

`textwidget.marks` is a dictionary-like object with mark names as keys and text
index namedtuples as values. Pythotk represents text indexes as namedtuples
that have `line` and `column` attributes, which is useful if you only need the
line. In tkinter, you need to parse the `'line.column'` string with
`.split('.')` and take the first element of the split result.

**Tkinter:**

```python3
cursor_lineno = int(textwidget.index('insert').split('.')[0])
```

**Pythotk:**

```python3
cursor_lineno = textwidget.marks['insert'].line
```

In tkinter you also need to construct the `'line.column'` strings yourself, but
in pythotk you can use `(line, column)` tuples.

**Tkinter:**

```python3
textwidget.mark_set('insert', '{}.{}'.format(new_cursor_line, new_cursor_column))
```

**Pythotk:**

```python3
textwidget.marks['insert'] = (new_cursor_line, new_cursor_column)
```

Tcl uses strings like `3.4 + 5 chars` to denote the position that is 5
characters after the position `3.4`. Pythotk's text position namedtuples have a
pythonic `forward()` method that returns a new text position.

**Tkinter:**

```python3
# textwidget.index always returns the position as 'line.column'
new_position = textwidget.index('{}.{} + 5 chars - 1 line'.format(line, column))
# now new_position is a string, and you may need to parse it back to
# separate line and column
```

**Pythotk:**

```python3
new_position = textwidget.index(line, column).forward(chars=5).back(lines=1)
# new_position is now a text position namedtuple
```


### Timeouts

In tkinter, `any_widget.after(1000, func)` runs `func()` after 1 second, and
the `any_widget` can be any tkinter widget. That's right, you need a widget for
scheduling timeouts. This can be a problem in library code. But what if during
that 1 second of waiting time, you decide that you don't want to run the
timeout after all? You can cancel the timeout, but as usual, pythotk makes it
easier.

**Tkinter:**

```python3
widget = get_some_widget_from_somewhere()
timeout_id = widget.after(1000, func)
...
# debugging
print(timeout_id)       # prints 'after#0'... very useful, eh??
...
if we_actually_dont_want_to_timeout():
    widget.after_cancel(timeout_id)
    print(timeout_id)   # still prints 'after#0'

# for debugging, print(timeout_id) prints something like after#0, which is not
# very useful at all
```

**Pythotk:**

```python3
timeout_object = tk.after(1000, func)
...
# debugging
print(timeout_object)   # prints <pending 'my_function' timeout 'after#0'>
...
if we_actually_dont_want_to_timeout():
    timeout.cancel()
    print(timeout)      # prints <cancelled 'my_function' timeout 'after#0'>
```
