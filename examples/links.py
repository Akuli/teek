import pythotk as tk
from pythotk.extras import links


window = tk.Window("Link Example")
text = tk.Text(window)
text.pack()

def lol():
    tk.dialog.info("Link Example Dialog", "Lol")

links.add_url_link(text, "Docs", 'https://pythotk.rtfd.io/')
text.insert(text.end, '\n\n')
links.add_url_link(text, "GitHub", 'https://github.com/Akuli/pythotk')
text.insert(text.end, '\n\n')
links.add_function_link(text, "Lol", lol)

tk.run()
