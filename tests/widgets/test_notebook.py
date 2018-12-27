import pytest

import pythotk as tk


class LolTab(tk.NotebookTab):
    pass


def test_reprs():
    notebook = tk.Notebook(tk.Window())

    label = tk.Label(notebook, "asd")
    label2 = tk.Label(notebook, "asdasd")
    tab = tk.NotebookTab(label, text='toot')
    tab2 = LolTab(label2, text='toot toot')
    assert repr(tab) == "NotebookTab(" + repr(label) + ", text='toot')"
    assert repr(tab2) == "LolTab(" + repr(label2) + ", text='toot toot')"

    assert repr(notebook) == '<pythotk.Notebook widget: contains 0 tabs>'
    notebook.append(tab)
    assert repr(notebook) == '<pythotk.Notebook widget: contains 1 tabs>'
    notebook.remove(tab)
    assert repr(notebook) == '<pythotk.Notebook widget: contains 0 tabs>'


def test_config_types(check_config_types):
    notebook = tk.Notebook(tk.Window())
    check_config_types(notebook.config, 'Notebook')

    tab = tk.NotebookTab(tk.Label(notebook, "asd"))
    notebook.append(tab)
    check_config_types(tab.config, 'NotebookTab')


def test_tab_object_caching():
    notebook = tk.Notebook(tk.Window())
    tab1 = tk.NotebookTab(tk.Label(notebook, "asd"))
    notebook.append(tab1)
    assert notebook[0] is tab1
    assert notebook.get_tab_by_widget(tab1.widget) is tab1


def test_initial_options():
    notebook = tk.Notebook(tk.Window())
    tab = tk.NotebookTab(tk.Label(notebook))

    with pytest.raises(RuntimeError):
        tab.config['text'] = 'lol'
    with pytest.raises(RuntimeError):
        tab.config['text']

    assert tab.initial_options == {}
    tab.initial_options['text'] = 'lol'
    notebook.append(tab)
    assert tab.config['text'] == 'lol'


def test_get_tab_by_widget_error():
    notebook = tk.Notebook(tk.Window())
    with pytest.raises(ValueError) as error:
        notebook.get_tab_by_widget(tk.Label(tk.Window(), text='lol'))

    assert str(error.value) == (
        "expected a widget with the notebook as its parent, "
        "got <pythotk.Label widget: text='lol'>")


def test_insert_with_different_indexes():
    notebook = tk.Notebook(tk.Window())

    notebook.insert(0, tk.NotebookTab(tk.Label(notebook, "1")))
    notebook.insert(1, tk.NotebookTab(tk.Label(notebook, "2")))
    notebook.insert(10, tk.NotebookTab(tk.Label(notebook, "3")))
    notebook.insert(-10, tk.NotebookTab(tk.Label(notebook, "0")))
    assert [tab.widget.config['text'] for tab in notebook] == list('0123')


def test_list_like_behaviour():
    notebook = tk.Notebook(tk.Window())
    tab1 = tk.NotebookTab(tk.Label(notebook, "1"))
    tab2 = tk.NotebookTab(tk.Label(notebook, "2"))
    tab3 = tk.NotebookTab(tk.Label(notebook, "3"))
    tab4 = tk.NotebookTab(tk.Label(notebook, "4"))
    tab5 = tk.NotebookTab(tk.Label(notebook, "5"))

    notebook.append(tab3)
    notebook.extend([tab4, tab5])
    notebook.insert(0, tab1)
    notebook.insert(1, tab2)
    assert list(notebook) == [tab1, tab2, tab3, tab4, tab5]

    assert notebook.pop() == tab5
    assert list(notebook) == [tab1, tab2, tab3, tab4]

    notebook[0] = tab5
    assert list(notebook) == [tab5, tab2, tab3, tab4]


def test_moves_only():
    notebook = tk.Notebook(tk.Window())
    tab1 = tk.NotebookTab(tk.Label(notebook, text="1"), text="One")
    tab2 = tk.NotebookTab(tk.Label(notebook, text="2"), text="Two")
    notebook.extend([tab1, tab2])
    tab1.config['text'] = 'wut1'
    tab2.config['text'] = 'wut2'

    notebook.insert(1, notebook[0])
    assert tab1.config['text'] == 'wut1'
    assert tab2.config['text'] == 'wut2'
    assert list(notebook) != [tab1, tab2]
    assert list(notebook) == [tab2, tab1]


def test_slicing_not_supported_error():
    notebook = tk.Notebook(tk.Window())
    catcher = pytest.raises(TypeError,
                            match=r'^slicing a Notebook is not supported$')
    with catcher:
        notebook[::-1]
    with catcher:
        notebook[:3] = 'lol wat'
    with catcher:
        del notebook[:3]


def test_hide_unhide_preserve_order():
    notebook = tk.Notebook(tk.Window())
    tabs = [tk.NotebookTab(tk.Label(notebook, str(n))) for n in [1, 2, 3]]
    notebook.extend(tabs)

    assert list(notebook) == tabs
    tabs[1].hide()
    assert list(notebook) == tabs
    tabs[1].unhide()
    assert list(notebook) == tabs


def test_move():
    notebook = tk.Notebook(tk.Window())
    tab1 = tk.NotebookTab(tk.Label(notebook, text="one"))
    tab2 = tk.NotebookTab(tk.Label(notebook, text="two"))
    notebook.extend([tab1, tab2])

    notebook.move(tab2, 0)
    assert list(notebook) == [tab2, tab1]
    notebook.move(tab2, 0)
    assert list(notebook) == [tab2, tab1]
    notebook.move(tab1, 0)
    assert list(notebook) == [tab1, tab2]
    notebook.move(tab1, 1)
    assert list(notebook) == [tab2, tab1]
    notebook.move(tab1, -1)     # some_list[-1] is last item
    assert list(notebook) == [tab2, tab1]
    notebook.move(tab1, -2)
    assert list(notebook) == [tab1, tab2]

    with pytest.raises(IndexError):
        notebook.move(tab1, 2)
    with pytest.raises(IndexError):
        notebook.move(tab1, -3)

    tab3 = tk.NotebookTab(tk.Label(notebook, text="three"))
    with pytest.raises(ValueError):
        notebook.move(tab3, 0)


def test_selected_tab():
    notebook = tk.Notebook(tk.Window())
    tab1 = tk.NotebookTab(tk.Label(notebook, text="one"))
    tab2 = tk.NotebookTab(tk.Label(notebook, text="two"))
    notebook.extend([tab1, tab2])
    assert notebook.selected_tab is tab1

    notebook.selected_tab = tab2
    assert notebook.selected_tab is tab2
    notebook.selected_tab = tab2    # intentionally repeated
    assert notebook.selected_tab is tab2

    notebook.clear()
    assert notebook.selected_tab is None


def test_insert_errors():
    window = tk.Window()
    notebook1 = tk.Notebook(window)
    label1 = tk.Label(notebook1, text="one")
    notebook2 = tk.Notebook(window)
    tab2 = tk.NotebookTab(tk.Label(notebook2, text="two"))

    with pytest.raises(ValueError) as error:
        notebook1.append(tab2)
    assert (repr(notebook2) + "'s tab") in str(error.value)
    assert str(error.value).endswith('to ' + repr(notebook1))

    # i imagine this will be a common mistake, so better be prepared to it
    with pytest.raises(TypeError) as error:
        notebook1.append(label1)
    assert str(error.value).startswith('expected a NotebookTab object')


def test_check_in_notebook():
    tab = tk.NotebookTab(tk.Label(tk.Notebook(tk.Window())))
    with pytest.raises(RuntimeError) as error:
        tab.hide()
    assert 'not in the notebook' in str(error.value)


def test_notebooktab_init_errors():
    notebook = tk.Notebook(tk.Window())
    label = tk.Label(notebook)

    lel_widget = tk.Window()
    with pytest.raises(ValueError) as error:
        tk.NotebookTab(lel_widget)
    assert ('widgets of NotebookTabs must be child widgets of a Notebook'
            in str(error.value))

    tk.NotebookTab(label)
    with pytest.raises(RuntimeError) as error:
        tk.NotebookTab(label)
    assert 'there is already a NotebookTab' in str(error.value)


def test_tab_added_with_tcl_call_so_notebooktab_object_is_created_automagic():
    notebook = tk.Notebook(tk.Window())
    label = tk.Label(notebook)
    tk.tcl_call(None, notebook, 'add', label)

    # looking up notebook[0] should create a new NotebookTab object
    assert isinstance(notebook[0], tk.NotebookTab)
    assert notebook[0] is notebook[0]   # and it should be "cached" now
