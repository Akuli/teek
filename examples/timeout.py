import tkinder as tk


class TimeoutWindow(tk.Window):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = None

        startbutton = tk.Button(self, "Start", command=self.start)
        startbutton.pack()
        cancelbutton = tk.Button(self, "Cancel", command=self.cancel)
        cancelbutton.pack()

    def start(self):
        if self.timeout is None:
            self.timeout = tk.after(3000, self.callback)
            print("running callback after 3 seconds")
        else:
            print("already started")

    def cancel(self):
        if self.timeout is None:
            print("already cancelled")
        else:
            self.timeout.cancel()
            self.timeout = None
            print("callback won't be ran")

    def callback(self):
        print("*** running the callback ***")
        self.timeout = None


tk.init()
window = TimeoutWindow()
window.on_close.connect(tk.quit)
tk.mainloop()
