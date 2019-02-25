import bs4

import teek
from teek.extras.soup import SoupViewer


html_string = """
<h1>Hello World!</h1>

<p>
    This is some HTML text.
    <strong>Bold</strong>, <em>italics</em> and stuff are supported.
    <a href="https://github.com/Akuli/teek">This is a link.</a>
</p>

<pre>print("this is some code")</pre>

<p>Text in <code>&lt;code&gt;</code> tags displays with monospace font. <br>
   It's easy to see the difference with the letter i:</p>

<p>Without a code tag:    iiiiiiiiii    <br>
   With a code tag: <code>iiiiiiiiii</code>
</p>

<p>This is teek's travis badge:
    <a href="https://travis-ci.org/Akuli/teek">
        <img src="https://travis-ci.org/Akuli/teek.svg?branch=master"
             alt="Build Status" /></a>
</p>

<p><i>ii</i><b>bb</b></p>
"""

teek.init_threads()     # image loading uses threads

window = teek.Window()
text = teek.Text(window, font=('', 11, ''))
text.pack(fill='both', expand=True)

viewer = SoupViewer(text)
viewer.create_tags()
for element in bs4.BeautifulSoup(html_string, 'lxml').body:
    viewer.add_soup(element)

window.on_delete_window.connect(teek.quit)
teek.run()

viewer.stop_loading(cleanup=True)
