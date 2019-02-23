import teek
from teek.extras import tooltips

window = teek.Window("Tooltip Example")
label = teek.Label(window, "I have a tooltip")
label.pack()
tooltips.set_tooltip(label, "This is the tooltip")

window.on_delete_window.connect(teek.quit)
teek.run()
