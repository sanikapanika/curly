from __future__ import print_function
import logging.handlers
import sys


if sys.version_info.major < 3:
    print("CurlFramework supports only Python3. Rerun application in Python3 environment.")
    exit(0)

from interpreter.CurlyInterpreter import CurlyInterpreter

log_handler = logging.handlers.RotatingFileHandler(filename="curlframework.log", maxBytes=500000)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s       %(message)s")
log_handler.setFormatter(log_formatter)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(log_handler)


def curlframework(argv):
    cfw = CurlyInterpreter()
    if len(argv[1:]):
        cfw.nonInteractive(argv)
    else:
        cfw.start()


if __name__ == "__main__":
    try:
        curlframework(sys.argv)
    except (KeyboardInterrupt, SystemExit):
        pass
