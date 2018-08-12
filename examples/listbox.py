import tkinder as tk


window = tk.Window("Listbox Example")

listbox = tk.Listbox(window, multiple=True)
listbox.pack()
listbox.extend(['a', 'b', 'c'])
for item in listbox:
    print(item)

window.on_delete_window.connect(tk.quit)
tk.run()
