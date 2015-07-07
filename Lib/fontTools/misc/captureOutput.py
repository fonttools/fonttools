import sys
from cStringIO import StringIO

class captureOutput(object):
    def __init__(self):
        self.backup = sys.stdout
        sys.stdout = StringIO()

    def __enter__(self):
        return self
    
    def getOutput(self):
        return sys.stdout.getvalue() 

    def __exit__(self, *_):
        sys.stdout.close()   
        sys.stdout = self.backup
