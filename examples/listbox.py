import tkinder as tk


tk.init()
window = tk.Window("Listbox Example")

listbox = tk.Listbox(window, multiple=True)
listbox.pack()
listbox.extend(['a', 'b', 'c'])
for item in listbox:
    print(item)

window.on_close.connect(tk.quit)
tk.mainloop()
