import pythotk as tk


def on_click():
    print("You clicked me!")


window = tk.Window()
button = tk.Button(window, "Click me", command=on_click)
button.pack()
tk.run()
