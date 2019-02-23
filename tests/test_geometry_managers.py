import pytest

import teek


def test_pack():
    window = teek.Window()
    button = teek.Button(window)
    button.pack(fill='both', expand=True)

    pack_info = button.pack_info()
    assert pack_info['in'] is window
    assert pack_info['side'] == 'top'
    assert pack_info['fill'] == 'both'
    assert pack_info['expand'] is True
    assert pack_info['anchor'] == 'center'

    for option in ['padx', 'pady']:
        assert isinstance(pack_info[option], list)
        assert len(pack_info[option]) in {1, 2}
        for item in pack_info[option]:
            assert isinstance(item, teek.ScreenDistance)
    for option in ['ipadx', 'ipady']:
        assert isinstance(pack_info[option], teek.ScreenDistance)

    button.pack_forget()
    with pytest.raises(teek.TclError):
        button.pack_info()

    button.pack(**pack_info)
    assert button.pack_info() == pack_info
    button.pack_forget()

    assert window.pack_slaves() == []
    label1 = teek.Label(window, 'label one')
    label1.pack()
    label2 = teek.Label(window, 'label two')
    label2.pack()
    assert window.pack_slaves() == [label1, label2]

    frame = teek.Frame(window)
    label2.pack(in_=frame)
    assert window.pack_slaves() == [label1]
    assert frame.pack_slaves() == [label2]


def test_grid():
    # grid shares a lot of code with pack, so no need to test everything
    # separately
    window = teek.Window()
    button = teek.Button(window)
    button.grid(column=1, rowspan=2, sticky='nswe')

    grid_info = button.grid_info()
    assert grid_info['column'] == 1
    assert grid_info['columnspan'] == 1
    assert grid_info['row'] == 0
    assert grid_info['rowspan'] == 2
    assert grid_info['in'] is button.parent
    assert grid_info['padx'] == grid_info['pady'] == [teek.ScreenDistance(0)]
    assert grid_info['ipadx'] == grid_info['ipady'] == teek.ScreenDistance(0)
    assert grid_info['sticky'] == 'nesw'     # not 'nswe' for some reason

    assert window.grid_slaves() == [button]


def test_grid_row_and_column_objects(check_config_types):
    window = teek.Window()
    assert window.grid_rows == []
    assert window.grid_columns == []

    # a new list is created every time
    assert window.grid_rows is not window.grid_rows
    assert window.grid_rows == window.grid_rows

    label = teek.Label(window)
    label.grid()

    for rows_columns in [window.grid_rows, window.grid_columns]:
        assert isinstance(rows_columns, list)
        assert len(rows_columns) == 1
        row_column = rows_columns[0]

        assert row_column.get_slaves() == [label]
        check_config_types(row_column.config, 'grid row or column object')

        row_column.config['weight'] = 4
        assert isinstance(row_column.config['weight'], float)
        assert row_column.config['weight'] == 4.0

        assert row_column == row_column
        assert row_column != 'toot'
        assert {row_column: 'woot'}[row_column] == 'woot'


def test_place():
    window = teek.Window()
    button = teek.Button(window)
    button.place(x=123, rely=0.5)

    place_info = button.place_info()
    assert place_info['anchor'] == 'nw'
    assert place_info['bordermode'] == 'inside'
    assert place_info['in'] is window
    assert place_info['x'] == teek.ScreenDistance(123)
    assert place_info['rely'] == 0.5

    assert isinstance(place_info['relx'], float)
    assert isinstance(place_info['rely'], float)
    assert isinstance(place_info['x'], teek.ScreenDistance)
    assert isinstance(place_info['y'], teek.ScreenDistance)

    assert place_info['width'] is None
    assert place_info['height'] is None
    assert place_info['relwidth'] is None
    assert place_info['relheight'] is None

    button.place_forget()
    assert button.place_info() == {}

    button.place(**place_info)
    assert button.place_info() == place_info
    button.place_forget()

    assert window.place_slaves() == []
    label1 = teek.Label(window, 'label one')
    label1.place(x=1)
    label2 = teek.Label(window, 'label two')
    label2.place(x=2)
    assert set(window.place_slaves()) == {label1, label2}   # allow any order

    frame = teek.Frame(window)
    label2.place(in_=frame)
    assert window.place_slaves() == [label1]
    assert frame.place_slaves() == [label2]


def test_place_special_error():
    label = teek.Label(teek.Window())
    with pytest.raises(TypeError) as error:
        label.place()

    assert str(error.value).startswith(
        "cannot call widget.place() without any arguments, do e.g. ")
