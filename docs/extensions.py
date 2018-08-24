import functools
import os
import re
import urllib.request     # because requests might not be installed

from docutils import nodes


@functools.lru_cache()
def check_url(url):
    # this is kind of slow on my system, so do nothing unless running in
    # readthedocs
    if os.environ.get('READTHEDOCS', None) != 'True':
        return

    print("\ndocs/extensions.py: checking if url exists: %s" % url)

    # this doesn't work with urllib's default User-Agent for some reason
    request = urllib.request.Request(url, headers={'User-Agent': 'asd'})
    response = urllib.request.urlopen(request)
    assert response.status == 200
    assert (b'The page you are looking for cannot be found.'
            not in response.read())


# there are urls like .../man/tcl8.6/... and .../man/tcl/...
# the non-8.6 ones always point to latest version, which is good because no
# need to hard-code version number
URL_TEMPLATE = 'https://www.tcl.tk/man/tcl/%s%s/%s.htm'

# because multiple functions are documented in the same man page
# for example, 'man Tk_GetBoolean' and 'man Tk_GetInt' open the same manual
# page on my system
MANPAGE_REDIRECTS = {
    'Tcl_GetBoolean': 'Tcl_GetInt',
}


def get_manpage_url(manpage_name, tcl_or_tk):
    manpage_name = MANPAGE_REDIRECTS.get(manpage_name, manpage_name)

    # c functions are named like Tk_GetColor, and the URLs only contain the
    # GetColor part for some reason
    is_c_function = manpage_name.startswith(tcl_or_tk.capitalize() + '_')

    # ik, this is weird
    if manpage_name.startswith('ttk_'):
        # ttk_separator --> ttk_separator
        name_part = manpage_name
    else:
        # tk_chooseColor --> chooseColor
        name_part = manpage_name.split('_')[-1]

    return URL_TEMPLATE % (tcl_or_tk.capitalize(),
                           'Lib' if is_c_function else 'Cmd',
                           name_part)


# i don't know how to use sphinx, i copy/pasted things from here:
# https://doughellmann.com/blog/2010/05/09/defining-custom-roles-in-sphinx/
def man_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    match = re.fullmatch(r'(\w+)\(3(tcl|tk)\)', text)
    assert match is not None, "invalid man page %r" % text
    manpage_name, tcl_or_tk = match.groups()

    url = get_manpage_url(manpage_name, tcl_or_tk)
    check_url(url)

    # this is the copy/pasta part
    node = nodes.reference(rawtext, text, refuri=url, **options)
    return [node], []


def setup(app):
    app.add_role('man', man_role)
