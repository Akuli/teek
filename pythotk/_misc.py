from pythotk._tcl_calls import tcl_call


def update(*, idletasks=False):
    """See :man:`update(3tk)`."""
    if idletasks:
        tcl_call(None, 'update', 'idletasks')
    else:
        tcl_call(None, 'update')
