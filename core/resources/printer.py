from __future__ import print_function
from __future__ import absolute_import

import threading
import sys
import collections
from weakref import WeakKeyDictionary

try:
    import queue
except:
    import Queue as queue

printer_queue = queue.Queue()
thread_output_stream = WeakKeyDictionary()

PrintResource = collections.namedtuple("PrintResource", ["content", "sep", "end", "file", "thread"])


class PrinterThread(threading.Thread):
    def __init__(self):
        super(PrinterThread, self).__init__()
        self.daemon = True

    def run(self):
        while True:
            content, sep, end, file_, thread = printer_queue.get()
            print(*content, sep=sep, end=end, file=file_)
            printer_queue.task_done()


def __cprint(*args, **kwargs):
    if not kwargs.pop("verbose", True):
        return

    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    thread = threading.current_thread()
    try:
        file_ = thread_output_stream.get(thread, ())[-1]
    except IndexError:
        file_ = kwargs.get("file", sys.stdout)

    printer_queue.put(PrintResource(content=args, sep=sep, end=end, file=file_, thread=thread))


def print_error(*args, **kwargs) -> None:
    __cprint("\033[91m[-]\033[0m", *args, **kwargs)


def print_status(*args, **kwargs) -> None:
    __cprint("\033[94m[*]\033[0m", *args, **kwargs)


def print_success(*args, **kwargs) -> None:
    __cprint("\033[92m[+]\033[0m", *args, **kwargs)


def print_info(*args, **kwargs) -> None:
    __cprint(*args, **kwargs)


def print_table(headers, *args, **kwargs) -> None:
    extra_fill = kwargs.get("extra_fill", 5)
    header_separator = kwargs.get("header_separator", "-")

    if not all(map(lambda x: len(x) == len(headers), args)):
        print_error("Headers and table rows tuples should be the same length.")
        return

    def custom_len(x):
        try:
            return len(x)
        except TypeError:
            return 0

    fill = []
    headers_line = '   '
    headers_separator_line = '   '
    for idx, header in enumerate(headers):
        column = [custom_len(arg[idx]) for arg in args]
        column.append(len(header))

        current_line_fill = max(column) + extra_fill
        fill.append(current_line_fill)
        headers_line = "".join((headers_line, "{header:<{fill}}".format(header=header, fill=current_line_fill)))
        headers_separator_line = "".join((
            headers_separator_line,
            "{:<{}}".format(header_separator * len(header), current_line_fill)
        ))

    print_info()
    print_info(headers_line)
    print_info(headers_separator_line)
    for arg in args:
        content_line = "   "
        for idx, element in enumerate(arg):
            if not isinstance(element, dict):
                content_line = "".join((
                    content_line,
                    "{:<{}}".format(element, fill[idx])
                ))
            else:
                content_line = "".join((
                    content_line,
                    "{:<{}}".format(print_dict(element), fill[idx])
                ))
        print_info(content_line)

    print_info()


def print_dict(dictionary) -> str:
    final_string = ''
    for key, val in dictionary.items():
        final_string += key + ": " + val
        if final_string != '':
            final_string += ", "

    return final_string

def pprint_dict_in_order(dictionary, order=None) -> None:
    order = order or ()

    def prettyprint(title, body):
        print_info("\n{}".format(title.capitalize()))
        if not isinstance(body, str):
            for value_element in body:
                print_info("- ", value_element)
        else:
            print_info(body)

    keys = list(dictionary.keys())
    for element in order:
        try:
            key = keys.pop(keys.index(element))
            value = dictionary[key]
        except (KeyError, ValueError):
            pass
        else:
            prettyprint(element, value)

    for rest_keys in keys:
        prettyprint(rest_keys, dictionary[rest_keys])


def color_blue(string: str) -> str:
    return "\033[94m{}\033[0m".format(string)


def color_green(string: str) -> str:
    return "\033[92m{}\033[0m".format(string)


def color_red(string: str) -> str:
    return "\033[91m{}\033[0m".format(string)
