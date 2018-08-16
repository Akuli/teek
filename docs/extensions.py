import functools
import re
import urllib.request     # because requests might not be installed

from docutils import nodes


@functools.lru_cache()
def check_url(url):
    print("\ndocs/extensions.py: checking if url exists: %s" % url)

    # this doesn't work with urllib's default User-Agent for some reason
    request = urllib.request.Request(url, headers={'User-Agent': 'asd'})
    assert urllib.request.urlopen(request).status == 200


URL_TEMPLATE = 'https://www.tcl.tk/man/tcl8.6/%sCmd/%s.htm'


# i don't know how to use sphinx, i copy/pasted things from here:
# https://doughellmann.com/blog/2010/05/09/defining-custom-roles-in-sphinx/
def man_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    match = re.fullmatch(r'(\w+)\(3(tcl|tk)\)', text)
    assert match is not None, "invalid man page %r" % text
    manpage_name, tcl_or_tk = match.groups()
    url = URL_TEMPLATE % (tcl_or_tk.capitalize(), manpage_name)
    check_url(url)

    # this is the copy/pasta part
    node = nodes.reference(rawtext, text, refuri=url, **options)
    return [node], []


def setup(app):
    app.add_role('man', man_role)
