import teek
from teek.extras import links


window = teek.Window("Link Example")
text = teek.Text(window)
text.pack()

def lol():
    teek.dialog.info("Link Example Dialog", "Lol")

links.add_url_link(text, "Docs", 'https://teek.rtfd.io/')
text.insert(text.end, '\n\n')
links.add_url_link(text, "GitHub", 'https://github.com/Akuli/teek')
text.insert(text.end, '\n\n')
links.add_function_link(text, "Lol", lol)

window.on_delete_window.connect(teek.quit)
teek.run()
