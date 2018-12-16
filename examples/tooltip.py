import pythotk as tk

window = tk.Window("Tooltip Example")
label = tk.Label(window, "I have a tooltip")
label.pack()
tk.extras.set_tooltip(label, "This is the tooltip")
tk.run()
