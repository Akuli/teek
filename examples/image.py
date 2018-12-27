import os

import pythotk as tk


IMAGE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'tests', 'data', 'smiley.gif')

window = tk.Window()
label = tk.Label(window, image=tk.Image(file=IMAGE_PATH),
                 text="Here's a smiley:", compound="bottom")
label.pack()
window.on_delete_window.connect(tk.quit)
tk.run()
