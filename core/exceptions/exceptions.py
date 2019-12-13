class CurlFrameworkException(Exception):
    def __init__(self, msg: str = ""):
        super(CurlFrameworkException, self).__init__(msg)


class OptionValidationError(CurlFrameworkException):
    pass


class StopThreadPoolExecutor(CurlFrameworkException):
    pass