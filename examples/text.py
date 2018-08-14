import tkinder


window = tkinder.Window()
window.title = "Text Widget Demo"

text = tkinder.Text(window)
text.pack(fill='both', expand=True)
text.insert(text.start, "hello world")

hello_tag = text.get_tag('hello_tag')
hello_tag['foreground'] = 'red'
hello_tag.add(text.start, text.start.forward(chars=5))

world_tag = text.get_tag('world_tag')
world_tag['foreground'] = 'green'
world_tag.add(text.end.back(chars=5), text.end)

# move cursor after hello
text.marks['insert'] = text.start.forward(chars=5)

window.on_delete_window.connect(tkinder.quit)
tkinder.run()
