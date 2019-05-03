import os
import time
import urllib.request

import pytest
bs4 = pytest.importorskip('bs4')    # noqa
pytest.importorskip('lxml')         # noqa

import teek
from teek.extras.soup import SoupViewer
pytest.importorskip('teek.extras.image_loader')


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
FIREFOX_SVG_URL = 'file://' + urllib.request.pathname2url(
    os.path.join(DATA_DIR, 'firefox.svg'))

# from test_image_loader.py
ignore_svglib_warnings = pytest.mark.filterwarnings(
    "ignore:The 'warn' method is deprecated")

big_html = '''
<h1>Header 1</h1>
<h2>Header 2</h2>
<h3>Header 3</h3>
<h4>Header 4</h4>
<h5>Header 5</h5>
<h6>Header 6</h6>

<p>The below code uses the <code>print</code> function.</p>

<pre>print("Hello World")</pre>

<p>Line<br>break</p>

<i>Italics 1</i><em>Italics 2</em>
<b>Bold 1</b><strong>Bold 2</strong>

<!-- this uses <P> instead of <p> to make sure it doesn't break anything
     bs4 should convert it to lowercase <p> -->
<P>This       contains

      many                   spaces</P>

<ul>
<li>One</li>
<li>Two</li>
<li>Three</li>
</ul>

<ol>
<li>One</li>
<li>Two</li>
<li>Three</li>
</ol>

<p><a href="https://example.com/">Link</a></p>

<img src="{FIREFOX_SVG_URL}" alt="firefox pic alt">
'''.format(FIREFOX_SVG_URL=FIREFOX_SVG_URL)


def get_tag_names(widget, string):
    # TODO: add search to teek
    start = teek.tcl_call(widget.TextIndex, widget, 'search', string, '1.0')
    end = start.forward(chars=len(string))
    tags = set(widget.get_all_tags(start))

    # must be same tags in the whole text
    index = start
    while index < end:
        assert set(widget.get_all_tags(index)) == tags
        index = index.forward(chars=1)

    return {tag.name[len('soup-'):] for tag in tags
            if tag.name.startswith('soup-')}


def create_souped_widget(html, **kwargs):
    widget = teek.Text(teek.Window())
    souper = SoupViewer(widget, **kwargs)
    souper.create_tags()
    for element in bs4.BeautifulSoup(html, 'lxml').body:
        souper.add_soup(element)

    return (souper, widget)


def test_tagging():
    souper, widget = create_souped_widget(big_html, threads=False)

    for h in '123456':
        assert get_tag_names(widget, 'Header ' + h) == {'h' + h}
    assert get_tag_names(widget, 'print') == {'p', 'code'}
    assert get_tag_names(widget, 'print(') == {'pre'}
    assert 'Line\nbreak' in widget.get()
    assert get_tag_names(widget, 'Italics 1') == {'i'}
    assert get_tag_names(widget, 'Italics 2') == {'em'}
    assert get_tag_names(widget, 'Bold 1') == {'b'}
    assert get_tag_names(widget, 'Bold 2') == {'strong'}
    assert 'This contains many spaces' in widget.get()
    assert get_tag_names(widget, '\N{bullet} One') == {'li', 'ul'}
    assert get_tag_names(widget, '1. One') == {'li', 'ol'}
    assert get_tag_names(widget, 'Link') == {'p', 'a'}
    assert get_tag_names(widget, 'firefox pic alt') == {'img'}


@pytest.mark.slow
def test_image_doesnt_load_without_threads():
    souper, widget = create_souped_widget(big_html, threads=False)
    assert 'firefox pic alt' in widget.get()

    end = time.time() + 0.5
    while time.time() < end:
        teek.update()
    assert 'firefox pic alt' in widget.get()


@ignore_svglib_warnings
@pytest.mark.slow
def test_image_loads_with_threads(deinit_threads):
    teek.init_threads()
    souper, widget = create_souped_widget(big_html)   # threads=True is default

    assert 'firefox pic alt' in widget.get()
    time.sleep(1)   # this used to be 0.1 and it made tests fail randomly
    teek.update()
    assert 'firefox pic alt' not in widget.get()


def test_unknown_tag():
    with pytest.warns(RuntimeWarning,
                      match=(r'contains a <script> tag.*'
                             r'no handle_script\(\) method')):
        souper, widget = create_souped_widget(
            '<body><script>console.log("hey")</script></body>', threads=False)
    assert widget.get() == 'console.log("hey")'
