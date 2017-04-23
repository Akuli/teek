import collections.abc
import sys
import traceback


def print_callback_traceback(stack_info):
    """Like traceback.print_exc(), but also show stack_info."""
    traceback_blabla, rest = traceback.format_exc().split('\n', 1)
    print(traceback_blabla, file=sys.stderr)
    print(stack_info + rest, end='', file=sys.stderr)


class MutableSet(collections.abc.MutableSet):
    """Like collections.abc.MutableSet, but implements missing methods."""

    # https://docs.python.org/3.4/library/stdtypes.html
    #
    # >>> set(dir(set)) - set(dir(collections.abc.MutableSet))
    # {'symmetric_difference_update', 'symmetric_difference', 'copy',
    #  'intersection', 'update', 'issuperset', 'union',
    #  'difference_update', 'intersection_update', 'difference',
    #  'issubset'}
    #
    # only some of these missing methods are implemented, let me know if
    # you want me to implement more of them

    def update(self, iterable):
        for element in iterable:
            self.add(element)
