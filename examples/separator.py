import teek


window = teek.Window()

teek.Label(window, "asd asd").pack()
teek.Separator(window).pack(fill='x')
teek.Label(window, "moar asd").pack()

window.on_delete_window.connect(teek.quit)
teek.run()
