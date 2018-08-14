import tkinder


window = tkinder.Window()

tkinder.Label(window, "asd asd").pack()
#tkinder.eval(None, 'pack [ttk::separator %s.sep] -fill x' % window.to_tcl())
tkinder.Separator(window).pack(fill='x')
print(dict(tkinder.Separator(window).config))
tkinder.Label(window, "moar asd").pack()

window.on_delete_window.connect(tkinder.quit)
tkinder.run()
