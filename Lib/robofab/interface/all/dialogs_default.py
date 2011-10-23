"""

    Dialog prototypes.
    
    These are loaded before any others. So if a specific platform implementation doesn't
    have all functions, these will make sure a NotImplemtedError is raised.
        
"""

__all__ = [
    "AskString",
    "AskYesNoCancel",
    "FindGlyph",
    "GetFile",
    "GetFolder",
    "Message",
    "OneList",
    "PutFile",
    "SearchList",
    "SelectFont",
    "SelectGlyph",
    "TwoChecks",
    "TwoFields",
    "ProgressBar",
]

# start with all the defaults. 

def AskString(prompt, value='', title='RoboFab'):
	"""Prototype for AskString dialog. Should show a prompt, a text input box and OK button."""
    raise NotImplementedError

def AskYesNoCancel(prompt, title='RoboFab', default=0):
	"""Prototype for AskYesNoCancel dialog. Should show a prompt, Yes, No, Cancel buttons."""
    raise NotImplementedError

def FindGlyph(font, message="Search for a glyph:", title='RoboFab'):
	"""Prototype for FindGlyph dialog. Should show a list of glyph names of the current font, OK and Cancel buttons"""
    raise NotImplementedError

def GetFile(message=None):
	"""Prototype for GetFile dialog. Should offer a standard OS get file dialog."""
    raise NotImplementedError

def GetFolder(message=None):
	"""Prototype for GetFolder dialog. Should offer a standard OS get folder dialog."""
    raise NotImplementedError

def Message(message, title='RoboFab'):
	"""Prototype for Message dialog. Should offer a window with the message, OK button."""
    raise NotImplementedError

def OneList(list, message="Select an item:", title='RoboFab'):
	"""Prototype for OneList dialog."""
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

