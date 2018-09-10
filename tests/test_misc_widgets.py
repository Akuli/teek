import pythotk as tk

import pytest


def test_button(capsys):
    window = tk.Window()
    stuff = []

    button1 = tk.Button(window)
    button2 = tk.Button(window, 'click me')
    button3 = tk.Button(window, 'click me', (lambda: stuff.append(3)))

    assert "text=''" in repr(button1)
    assert "text='click me'" in repr(button2)
    assert "text='click me'" in repr(button3)

    assert button1.config['text'] == ''
    assert button2.config['text'] == button3.config['text'] == 'click me'

    for button in [button1, button2, button3]:
        assert isinstance(button.config['command'], tk.Callback)
        with pytest.raises(ValueError) as error:
            button.config['command'] = print
        assert str(error.value) == (
            "cannot set the value of 'command', "
            "maybe use widget.config['command'].connect() instead?")

    # ideally there would be some way to click the button virtually and
    # let tk handle it, but i haven't gotten anything like that to work
    button1.config['command'].run()
    button2.config['command'].run()
    assert stuff == []
    button3.config['command'].run()
    assert stuff == [3]

    button1.config['command'].connect(stuff.append, args=[1])
    button2.config['command'].connect(stuff.append, args=[2])
    button3.config['command'].connect(stuff.append, args=['wolo'])
    button3.config['command'].connect(stuff.append, args=['wolo'])

    stuff.clear()
    for button in [button1, button2, button3]:
        button.config['command'].run()
    assert stuff == [1, 2, 3, 'wolo', 'wolo']

    def oops():
        raise ValueError("shit")

    assert capsys.readouterr() == ('', '')
    button1.config['command'].connect(oops)
    button1.config['command'].run()
    output, errors = capsys.readouterr()
    assert not output
    assert "button1.config['command'].connect(oops)" in errors


def test_button_invoke():
    button = tk.Button(tk.Window())
    stuff = []
    button.config['command'].connect(stuff.append, args=[1])
    button.config['command'].connect(stuff.append, args=[2])
    button.invoke()
    assert stuff == [1, 2]


def test_checkbutton():
    assert tk.Checkbutton(tk.Window()).config['text'] == ''
    assert tk.Checkbutton(tk.Window(), 'asd').config['text'] == 'asd'

    asd = []

    checkbutton = tk.Checkbutton(tk.Window(), 'asd', asd.append)
    checkbutton.config['command'].connect(asd.append)
    checkbutton.invoke()
    assert checkbutton.config['variable'].get() is True
    checkbutton.invoke()
    assert checkbutton.config['variable'].get() is False
    assert asd == [True, True, False, False]
    asd.clear()

    checkbutton = tk.Checkbutton(tk.Window(), 'asd', asd.append,
                                 onvalue=False, offvalue=True)
    checkbutton.config['command'].connect(asd.append)
    checkbutton.invoke()
    assert checkbutton.config['variable'].get() is False
    checkbutton.invoke()
    assert checkbutton.config['variable'].get() is True
    assert asd == [False, False, True, True]
    asd.clear()


def test_entry():
    entry = tk.Entry(tk.Window(), "some text")
    assert "text='some text'" in repr(entry)

    assert entry.text == 'some text'
    entry.text = 'new text'
    assert entry.text == 'new text'
    assert "text='new text'" in repr(entry)

    assert entry.cursor_pos == len(entry.text)
    entry.cursor_pos = 0
    assert entry.cursor_pos == 0

    assert entry.config['exportselection'] is True
    assert isinstance(entry.config['width'], int)


def test_label():
    window = tk.Window()

    label = tk.Label(window)
    assert "text=''" in repr(label)
    assert label.config['text'] == ''

    label.config.update({'text': 'new text'})
    assert label.config['text'] == 'new text'
    assert "text='new text'" in repr(label)

    label2 = tk.Label(window, 'new text')
    assert label.config == label2.config


def test_labelframe():
    assert tk.LabelFrame(tk.Window()).config['text'] == ''
    assert tk.LabelFrame(tk.Window(), 'hello').config['text'] == 'hello'

    labelframe = tk.LabelFrame(tk.Window(), 'hello')
    assert repr(labelframe) == "<pythotk.LabelFrame widget: text='hello'>"


def test_progressbar():
    progress_bar = tk.Progressbar(tk.Window())
    assert progress_bar.config['value'] == 0

    # test that bouncy methods don't raise errors, they are tested better below
    progress_bar.config['mode'] = 'indeterminate'
    progress_bar.start()
    progress_bar.stop()


@pytest.mark.slow
def test_progressbar_bouncing():
    progress_bar = tk.Progressbar(tk.Window(), mode='indeterminate')
    assert progress_bar.config['value'] == 0
    progress_bar.start()

    def done_callback():
        try:
            # sometimes the value gets set to 3 on this laptop, so this works
            assert progress_bar.config['value'] > 2
            progress_bar.stop()     # prevents funny tk errors
        finally:
            # if this doesn't run, the test freezes
            tk.quit()

    tk.after(500, done_callback)
    tk.run()


def test_scrollbar(handy_callback):
    scrollbar = tk.Scrollbar(tk.Window())
    assert scrollbar.get() == (0.0, 1.0)

    # testing the set method isn't as easy as you might think because get()
    # doesn't return the newly set arguments after calling set()
    @handy_callback
    def asd(*args):
        assert args == ('set', '1.2', '3.4')

    asd_command = tk.create_command(asd, extra_args_type=str)
    tk.tcl_call(None, 'rename', scrollbar.to_tcl(), 'real_scrollbar')
    tk.tcl_call(None, 'rename', asd_command, scrollbar.to_tcl())
    try:
        scrollbar.set(1.2, 3.4)
        assert asd.ran_once()
    finally:
        tk.delete_command(scrollbar.to_tcl())
        tk.tcl_call(None, 'rename', 'real_scrollbar', scrollbar.to_tcl())

    # this tests the code that runs when the user scrolls the scrollbar
    log = []
    scrollbar.config['command'].connect(lambda *args: log.append(args))

    tk.tcl_eval(None, '''
    set command [%s cget -command]
    $command moveto 1.2
    $command scroll 1 units
    $command scroll 2 pages
    ''' % scrollbar.to_tcl())
    assert log == [
        ('moveto', 1.2),
        ('scroll', 1, 'units'),
        ('scroll', 2, 'pages')
    ]


def test_separator():
    hsep = tk.Separator(tk.Window())
    vsep = tk.Separator(tk.Window(), orient='vertical')
    assert hsep.config['orient'] == 'horizontal'
    assert vsep.config['orient'] == 'vertical'
    assert repr(hsep) == "<pythotk.Separator widget: orient='horizontal'>"
    assert repr(vsep) == "<pythotk.Separator widget: orient='vertical'>"


def test_spinbox():
    asd = []
    spinbox = tk.Spinbox(tk.Window(), command=(lambda: asd.append('boo')))
    assert asd == []
    tk.tcl_eval(None, '''
    set command [%s cget -command]
    $command
    $command
    ''' % spinbox.to_tcl())
    assert asd == ['boo', 'boo']
