import teek


class Paint:

    def __init__(self, window):
        self.canvas = teek.Canvas(window, bg='white')
        self.canvas.bind('<Button-1>', self.begin_draw, event=True)
        self.canvas.bind('<B1-Motion>', self.do_draw, event=True)
        self.canvas.bind('<ButtonRelease-1>', self.end_draw)
        self._previous_mouse_xy = None

    def begin_draw(self, event):
        self._previous_mouse_xy = (event.x, event.y)

    def do_draw(self, event):
        self.canvas.create_line(
            self._previous_mouse_xy[0], self._previous_mouse_xy[1],
            event.x, event.y)
        self._previous_mouse_xy = (event.x, event.y)

    def end_draw(self):
        self._previous_mouse_xy = None


window = teek.Window()

paint = Paint(window)
paint.canvas.pack()

window.on_delete_window.connect(teek.quit)
teek.run()
