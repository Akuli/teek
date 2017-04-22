import tkinder as tk


def on_click():
    print("You clicked me!")


tk.init()
window = tk.Window()
button = tk.Button(window, "Click me", command=on_click)
button.pack()
window.on_close.connect(tk.quit)
tk.mainloop()
