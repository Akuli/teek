import os

import teek


IMAGE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'tests', 'data', 'smiley.gif')

window = teek.Window()
label = teek.Label(window, image=teek.Image(file=IMAGE_PATH),
                   text="Here's a smiley:", compound="bottom")
label.pack()
window.on_delete_window.connect(teek.quit)
teek.run()
