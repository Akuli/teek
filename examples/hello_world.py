import teek as tk


window = tk.Window("Hello")
label = tk.Label(window, "Hello World!")
label.pack()
window.on_delete_window.connect(tk.quit)
tk.run()
