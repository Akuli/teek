import tkinder as tk


tk.init()
window = tk.Window("Hello")
label = tk.Label(window, "Hello World!")
label.pack()
window.on_close.connect(tk.quit)
tk.mainloop()
