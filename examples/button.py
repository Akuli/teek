import teek


def on_click():
    print("You clicked me!")


window = teek.Window()
button = teek.Button(window, "Click me", command=on_click)
button.pack()
window.on_delete_window.connect(teek.quit)
teek.run()
