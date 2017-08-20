# Tkinder

Tkinder is a more pythonic and user-friendly alternative to Python's
tkinter module. It doesn't come with Python so you need to install it
yourself, but it's nice and light-weight.

## Hello World!

```python
import tkinder as tk

window = tk.Window("Hello")
label = tk.Label(window, "Hello World!")
label.pack()
window.on_delete_window.connect(tk.quit)
tk.run()
```

That's it. Even people with no Tk experience understand how this code
works because there is no magic `root` variable, and the window class is
named `Window` instead of `Tk` or `Toplevel`.
