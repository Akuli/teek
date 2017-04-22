import sys
import traceback


def print_callback_traceback(stack_info):
    """Like traceback.print_exc(), but also show stack_info."""
    traceback_blabla, rest = traceback.format_exc().split('\n', 1)
    print(traceback_blabla, file=sys.stderr)
    print(stack_info + rest, end='', file=sys.stderr)
