import teek
from teek.extras import links


def lol():
    teek.dialog.info("Link Example Dialog", "Lol")


window = teek.Window("Link Example")
text = teek.Text(window)
text.pack()

old_end = text.end
text.insert(text.end, "Docs")
links.add_url_link(text, 'https://teek.rtfd.io/', old_end, text.end)
text.insert(text.end, '\n\n')

old_end = text.end
text.insert(text.end, "GitHub")
links.add_url_link(text, 'https://github.com/Akuli/teek', old_end, text.end)
text.insert(text.end, '\n\n')

old_end = text.end
text.insert(text.end, "Lol")
links.add_function_link(text, lol, old_end, text.end)
text.insert(text.end, '\n\n')

window.on_delete_window.connect(teek.quit)
teek.run()
