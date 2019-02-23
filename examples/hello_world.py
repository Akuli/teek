import teek


window = teek.Window("Hello")
label = teek.Label(window, "Hello World!")
label.pack()
window.on_delete_window.connect(teek.quit)
teek.run()
