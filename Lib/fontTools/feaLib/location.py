class FeatureLibLocation(object):
    """A location in a feature file"""
    def __init__(self, file, line, column):
        self.file = file
        self.line = line
        self.column = column

    def __str__(self):
    		return "%s:%i:%i" % (self.file, self.line, self.column)
