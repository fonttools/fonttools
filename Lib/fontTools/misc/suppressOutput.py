import os

class suppressOutput(object):
    '''
    Supress all contents from stdout and stderr
    '''
    def __init__(self):
        self.null =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        self.backup = (os.dup(1), os.dup(2))

    def __enter__(self):
        os.dup2(self.null[0],1)
        os.dup2(self.null[1],2)

    def __exit__(self, *_):
        os.dup2(self.backup[0],1)
        os.dup2(self.backup[1],2)
        os.close(self.null[0])
        os.close(self.null[1])
