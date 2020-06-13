class OTLLibError(Exception):
    def __init__(self, message, location):
        Exception.__init__(self, message)
        self.location = location

    def __str__(self):
        message = Exception.__str__(self)
        if self.location:
            if hasattr(self.location, "__iter__") and not isinstance(
                self.location, str
            ):
                loc = ":".join([str(x) for x in self.location])
            else:
                loc = self.location
            return f"{loc}: {message}"
        else:
            return message
