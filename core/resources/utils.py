import os
import importlib
from functools import wraps

import core.modules as cfw_modules
import core.resources as resources
import templates

from core.exceptions.exceptions import CurlFrameworkException
from core.resources.printer import print_error

MODULES_DIR = cfw_modules.__path__[0]
RESOURCES_DIR = resources.__path__[0]
TEMPLATES_DIR = templates.__path__[0]


def index_modules(modules_directory: str = MODULES_DIR) -> list:
    modules = []
    for root, dirs, files in os.walk(modules_directory):
        _, package, root = root.rpartition("core/".replace("/", os.sep))
        root = root.replace(os.sep, ".")
        files = filter(lambda x: not x.startswith("__") and x.endswith(".py"), files)
        modules.extend(map(lambda x: ".".join((root, os.path.splitext(x)[0])), files))

    return modules


def index_templates(templates_directory: str = TEMPLATES_DIR) -> list:
    saved_templ = []
    for root, dirs, files in os.walk(templates_directory):
        _, package, root = root.rpartition("templates/".replace("/", os.sep))
        root = root.replace(os.sep, ".")
        files = filter(lambda x: x.endswith(".json"), files)
        saved_templ.extend(map(lambda x: ".".join((root, os.path.splitext(x)[0])), files))

    return saved_templ

def filter_modules(x):
    if not x.startswith("__") and x.endswith(".py"):
        return True
    else:
        return False


def pythonize_path(path: str) -> str:
    return path.replace("/", ".")


def import_template(path: str):
    try:
        module = importlib.import_module(path)
        if hasattr(module, "Request"):
            return getattr(module, "Request")
        else:
            raise ImportError("No module named '{}'".format(path))

    except (ImportError, AttributeError, KeyError) as err:
        raise CurlFrameworkException(
            "Error during loading '{}'\n\n"
            "Error: {}\n\n"
            "It should be a valid path to the module. "
            "Use <tab> key multiple times for completion.".format(humanize_path(path), err)
        )


def humanize_path(path: str) -> str:
    return path.replace(".", "/")


def module_required(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self.current_module:
            print_error("You have to activater any module with 'use' command.")
            return
        return fn(self, *args, **kwargs)

    try:
        name = "module_required"
        wrapper.__decorators__.append(name)
    except AttributeError:
        wrapper.__decorators__ = [name]
    return wrapper


def stop_after(space_number):
    def _outer_wrapper(wrapped_function):
        @wraps(wrapped_function)
        def _wrapper(self, *args, **kwargs):
            try:
                if args[1].count(" ") == space_number:
                    return []
            except Exception as err:
                print_error(err)
            return wrapped_function(self, *args, **kwargs)

        return _wrapper

    return _outer_wrapper
