"""

    Dialogs for FontLab < 5.1. 
    
    This one should be loaded for various platforms, using dialogKit
    http://www.robofab.org/tools/dialogs.html
    
"""

from FL import *
from dialogKit import ModalDialog, Button, TextBox, EditText

__all__ = [
    "AskString",
    "AskYesNoCancel",
    #"FindGlyph",
    "GetFile",
    "GetFolder",
    "Message",
    "OneList",
    "PutFile",
    #"SearchList",
    #"SelectFont",
    #"SelectGlyph",
    #"TwoChecks",
    #"TwoFields",
    "ProgressBar",
]


def AskString(message, value='', title='RoboFab'):
    dialogInstance = _AskStringDialog(message, value, title)
    return dialogInstance.getValue()

class _AskStringDialog(object):
    def __init__(self, message, value, title):
        self.w = ModalDialog((360, 140), title)
        self.w.button1 = Button((-100, -300, 80, 24), 'OK', callback=self.buttonCallback)
        self.w.t = TextBox((5, 10, -5, 27), message)
        self.w.inputValue = EditText((5, 35, -5, 50), value)
        self.w.open()
    
    def getValue(self):
        return self.w.inputValue.get()
    
    def buttonCallback(self, sender):
        self.w.close()

def AskYesNoCancel(message, title='RoboFab', default=1, informativeText=None):
    dialogInstance = _AskYesNoCancelDialog(message, title=title, default=default)
    result = dialogInstance.getValue()
    if result is None and default is not None:
        return default
    return result

class _AskYesNoCancelDialog(object):
    def __init__(self, message, default=None, title="RoboFab"):
        # default is ignord?
        self.answer = -1
        self.w = ModalDialog((360, 140), title, okCallback=self.buttonOKCallback)
        self.w.noButton = Button((10, -35, 80, 24), 'No', callback=self.buttonNoCallback)
        self.w.t = TextBox((5, 10, -5, 27), message)
        self.w.open()
    
    def getValue(self):
        return self.answer
    
    def buttonNoCallback(self, sender):
        self.answer = 0
        self.w.close()
        
    def buttonOKCallback(self, sender):
        self.answer = 1
        self.w.close()

def FindGlyph(aFont, message="Search for a glyph:", title='RoboFab'):
    raise NotImplementedError

def GetFile(message=None, title=None, directory=None, fileName=None, allowsMultipleSelection=False, fileTypes=None):
    strFilter = "All Files  (*.*)|*.*|"
    defaultExt = ""
    # using fontlab's internal file dialogs
    return fl.GetFileName(1, defaultExt, message, strFilter)

def GetFolder(message=None, title=None, directory=None, allowsMultipleSelection=False):
    # using fontlab's internal file dialogs
    if message is None:
        message = ""
    return fl.GetPathName(message)

def Message(message, title='RoboFab', informativeText=None):
    """ Display a standard message dialog.
        Note: informativeText is not supported on this platform.
    """
    if informativeText is not None:
        message = "%s\n%s"%(message, informativeText)
    _MessageDialog(message, title)
    
class _MessageDialog(object):
    def __init__(self, message, title):
        self.w = ModalDialog((360, 100), title)
        self.w.t = TextBox((5, 10, -5, -40), message)
        self.w.open()

    
def PutFile(message=None, fileName=None):
    # using fontlab's internal file dialogs
    # message is not used
    if message is None:
        message = ""
    if fileName is None:
        fileName = ""
    defaultExt = ""
    return fl.GetFileName(0, defaultExt, fileName, '')

def OneList(list, message="Select an item:", title='RoboFab'):
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

    def __init__(self, title="RoboFab...", ticks=0, label=""):
        self._tickValue = 1
        fl.BeginProgress(title, ticks)

    def getCurrentTick(self):
        return self._tickValue

    def tick(self, tickValue=None):
        if not tickValue:
            tickValue = self._tickValue
        fl.TickProgress(tickValue)
        self._tickValue = tickValue + 1

    def label(self, label):
        pass

    def close(self):
        fl.EndProgress()

