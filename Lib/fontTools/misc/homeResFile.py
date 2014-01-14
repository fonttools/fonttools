"""Mac-only module to find the home file of a resource."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
import array
import calldll
import macfs, Res


def HomeResFile(res):
	"""Return a path to the file in which resource 'res' lives."""
	return GetFileLocation(res.HomeResFile())


def GetFileLocation(refNum):
	"""Return a path to the open file identified with refNum."""
	pb = ParamBlock(refNum)
	return pb.getPath()

#
# Internal cruft, adapted from MoreFiles
#

_InterfaceLib = calldll.getlibrary("InterfaceLib")
GetVRefNum = calldll.newcall(_InterfaceLib.GetVRefNum, "None", "InShort", "OutShort")
_getInfo = calldll.newcall(_InterfaceLib.PBGetFCBInfoSync, "Short", "InLong")


_FCBPBFormat = """
	qLink:        l
	qType:        h
	ioTrap:       h
	ioCmdAddr:    l
	ioCompletion: l
	ioResult:     h
	ioNamePtr:    l
	ioVRefNum:    h
	ioRefNum:     h
	filler:       h
	ioFCBIndx:    h
	filler1:      h
	ioFCBFINm:    l
	ioFCBFlags:   h
	ioFCBStBlk:   h
	ioFCBEOF:     l
	ioFCBPLen:    l
	ioFCBCrPs:    l
	ioFCBVRefNum: h
	ioFCBClpSiz:  l
	ioFCBParID:   l
"""

class ParamBlock(object):
	
	"""Wrapper for the very low level FCBPB record."""
	
	def __init__(self, refNum):
		self.__fileName = array.array("c", "\0" * 64)
		sstruct.unpack(_FCBPBFormat, 
				"\0" * sstruct.calcsize(_FCBPBFormat), self)
		self.ioNamePtr = self.__fileName.buffer_info()[0]
		self.ioRefNum = refNum
		self.ioVRefNum = GetVRefNum(refNum)
		self.__haveInfo = 0
	
	def getInfo(self):
		if self.__haveInfo:
			return
		data = sstruct.pack(_FCBPBFormat, self)
		buf = array.array("c", data)
		ptr = buf.buffer_info()[0]
		err = _getInfo(ptr)
		if err:
			raise Res.Error("can't get file info", err)
		sstruct.unpack(_FCBPBFormat, buf.tostring(), self)
		self.__haveInfo = 1
	
	def getFileName(self):
		self.getInfo()
		data = self.__fileName.tostring()
		return data[1:byteord(data[0])+1]
	
	def getFSSpec(self):
		self.getInfo()
		vRefNum = self.ioVRefNum
		parID = self.ioFCBParID
		return macfs.FSSpec((vRefNum, parID, self.getFileName()))
	
	def getPath(self):
		return self.getFSSpec().as_pathname()


if __name__ == "__main__":
	fond = Res.GetNamedResource("FOND", "Helvetica")
	print(HomeResFile(fond))
