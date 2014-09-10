#this file include all the program states
class States(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
