import teek
from teek.extras import cross_platform


def test_bind_tab_key():
    what_happened = []

    def callback1(shifted):
        what_happened.append((1, shifted))

    def callback2(shifted, event):
        assert event == 'fake event'
        what_happened.append((2, shifted))

    widget = teek.Window()
    cross_platform.bind_tab_key(widget, callback1)
    cross_platform.bind_tab_key(widget, callback2, event=True)

    # might be nice to trigger a warning when attempting to use <Shift-Tab>
    # on x11
    widget.bindings['<Tab>'].run('fake event')
    if teek.windowingsystem() == 'x11':
        widget.bindings['<ISO_Left_Tab>'].run('fake event')
    else:
        widget.bindings['<Shift-Tab>'].run('fake event')

    assert what_happened == [
        (1, False), (2, False),
        (1, True), (2, True),
    ]
