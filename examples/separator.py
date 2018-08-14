import tkinder


window = tkinder.Window()

tkinder.Label(window, "asd asd").pack()
tkinder.Separator(window).pack(fill='x')
tkinder.Label(window, "moar asd").pack()

window.on_delete_window.connect(tkinder.quit)
tkinder.run()
