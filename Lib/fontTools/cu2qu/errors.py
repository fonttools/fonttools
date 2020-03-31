
class Error(Exception):
    """Base Cu2Qu exception class for all other errors."""


class ApproxNotFoundError(Error):
    def __init__(self, curve):
        message = "no approximation found: %s" % curve
        super(Error, self).__init__(message)
        self.curve = curve
