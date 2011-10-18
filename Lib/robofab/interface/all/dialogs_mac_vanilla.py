"""

    Dialogs for environments that support cocao / vanilla.

"""

__all__ = [
#    "AskString",
    "AskYesNoCancel",
#    "FindGlyph",
#    "GetFile",
#    "GetFolder",
    "Message",
#    "OneList",
    "PutFile",
#    "SearchList",
#    "SelectFont",
#    "SelectGlyph",
#    "TwoChecks",
#    "TwoFields",
#    "ProgressBar",
]


# start with all the defaults. 

def AskString(prompt, value='', title='RoboFab'):
    raise NotImplementedError

def AskYesNoCancel(prompt, title='RoboFab', default=0, informativeText=""):
    import vanilla.dialogs
    vanilla.dialogs.askYesNoCancel(messageText=prompt, informativeText=additionalText, resultCallback=_resultCallback)

def FindGlyph(aFont, message="Search for a glyph:", title='RoboFab'):
    raise NotImplementedError

def GetFile(message=None):
    raise NotImplementedError

def GetFolder(message=None):
    raise NotImplementedError

def Message(message, title='RoboFab', informativeText=""):
    import vanilla.dialogs
    vanilla.dialogs.message(messageText=message, informativeText=informativeText)
    
def OneList(list, message="Select an item:", title='RoboFab'):
    raise NotImplementedError
    
def PutFile(message=None, defaultName=None):
    raise NotImplementedError

def SearchList(list, message="Select an item:", title='RoboFab'):
    raise NotImplementedError

def SelectFont(message="Select a font:", title='RoboFab'):
    raise NotImplementedError

def SelectGlyph(font, message="Select a glyph:", title='RoboFab'):
    raise NotImplementedError

def TwoChecks(title_1="One",  title_2="Two", value1=1, value2=1, title='RoboFab'):
    raise NotImplementedError

def TwoFields(title_1="One:", value_1="0", title_2="Two:", value_2="0", title='RoboFab'):
    raise NotImplementedError

class ProgressBar(object):
    pass

