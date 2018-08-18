from pythotk._tcl_calls import call


def update(*, idletasks=False):
    """See :man:`update(3tk)`."""
    if idletasks:
        call(None, 'update', 'idletasks')
    else:
        call(None, 'update')
