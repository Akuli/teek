import pythotk as tk
from pythotk.extras import tooltips

window = tk.Window("Tooltip Example")
label = tk.Label(window, "I have a tooltip")
label.pack()
tooltips.set_tooltip(label, "This is the tooltip")

window.on_delete_window.connect(tk.quit)
tk.run()
