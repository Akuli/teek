import teek


def on_check_or_uncheck(checked):
    if checked:
        print("Checked")
    else:
        print("Unchecked")


window = teek.Window("Checkbutton Example")
teek.Checkbutton(window, "Check me", on_check_or_uncheck).pack()
window.on_delete_window.connect(teek.quit)
teek.run()
