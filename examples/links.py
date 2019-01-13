import teek as tk
from teek.extras import links


window = tk.Window("Link Example")
text = tk.Text(window)
text.pack()

def lol():
    tk.dialog.info("Link Example Dialog", "Lol")

links.add_url_link(text, "Docs", 'https://teek.rtfd.io/')
text.insert(text.end, '\n\n')
links.add_url_link(text, "GitHub", 'https://github.com/Akuli/teek')
text.insert(text.end, '\n\n')
links.add_function_link(text, "Lol", lol)

window.on_delete_window.connect(tk.quit)
tk.run()
