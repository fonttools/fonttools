

class OpentypeLibError(Exception):
    def __init__(self, message, location):
        Exception.__init__(self, message)
        self.location = location

    def __str__(self):
        message = Exception.__str__(self)
        if self.location:
            path, line, column = self.location
            return f"{path}:{line}:{column}: {message}"
        else:
            return message
