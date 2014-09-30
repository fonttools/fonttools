from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.misc.fixedTools import fixedToFloat as fi2fl, floatToFixed as fl2fi
from . import DefaultTable
import struct

class FeatureName(object):
	def __init__(self, *args):
		if len(args) == 4:
			self.feature = args[0]
			self.featureFlags = args[1]
			self.nameIndex = args[2]
			self.settings = args[3]

	def toXML(self, writer, ttFont):
		writer.begintag("feature", [('type', self.feature), ('featureFlags', '0x'+'{:04X}'.format(self.featureFlags)),('nameIndex', self.nameIndex)])
		writer.newline()
		for s in self.settings:
			s.toXML(writer, ttFont)
		writer.endtag("feature")
		writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		self.feature = safeEval(attrs["type"])
		self.featureFlags = safeEval(attrs["featureFlags"])
		self.nameIndex = safeEval(attrs["nameIndex"])
		self.settings = []
		for element in content:
			if isinstance(element, tuple):
				setting = SettingName()
				self.settings.append(setting)
				name, attrs, content = element
				setting.fromXML(name, attrs, content, ttFont)

	def __repr__(self):
		return "<FeatureName type=%d; featureFlags=%s; nameIndex=%d>" % (
				self.feature, '0x'+'{:04X}'.format(self.featureFlags), self.nameIndex)

class SettingName(object):
	def __init__(self, *args):
		if len(args) == 2:
			self.setting = args[0]
			self.nameIndex = args[1]

	def toXML(self, writer, ttFont):
		writer.simpletag("setting", [('type', self.setting), ('nameIndex', self.nameIndex)])
		writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		self.setting = safeEval(attrs["type"])
		self.nameIndex = safeEval(attrs["nameIndex"])

	def __repr__(self):
		return "<SettingName type=%d; nameIndex=%d>" % (
				self.setting, self.nameIndex)

class table__f_e_a_t(DefaultTable.DefaultTable):
	
	dependencies = ['name']
	
	def decompile(self, data, ttFont):
		version, featureNameCount = struct.unpack(">LH", data[:6])
		self.version = fi2fl(version, 16)
		assert data[6:12] == "\0\0\0\0\0\0"
		data = data[12:]
		self.names = []
		for i in range(featureNameCount):
			feature, nSettings, settingTable, featureFlags, nameIndex = struct.unpack(">HHLHh", data[:12])
			self.names.append(FeatureName(feature, featureFlags, nameIndex, (nSettings, settingTable)))
			data = data[12:]
		for i in range(featureNameCount):
			offset = self.names[i].settings[1] - (12+12*featureNameCount)
			settings = []
			for j in range(self.names[i].settings[0]):
				setting, nameIndex = struct.unpack(">Hh", data[offset+j*4:offset+(j+1)*4])
				settings.append(SettingName(setting, nameIndex))
			self.names[i].settings = settings
		self.data = data

	def compile(self, ttFont):
		featureNameCount = len(self.names)
		data = struct.pack(">LH", fl2fi(self.version, 16), featureNameCount)
		data += "\0\0\0\0\0\0"
		data2 = ""
		offset = 12+12*featureNameCount
		settingsCount = 0
		for n in self.names:
			nSettings = len(n.settings)
			data += struct.pack(">HHLHh", n.feature, nSettings, offset+settingsCount*4, n.featureFlags, n.nameIndex)
			for s in n.settings:
				data2 += struct.pack(">Hh", s.setting, s.nameIndex)
				settingsCount += 1
		return data+data2

	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		writer.begintag("names")
		writer.newline()
		for n in self.names:
			n.toXML(writer, ttFont)
		writer.endtag("names")
		writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name == "version":
			self.version = safeEval(attrs["value"])
		elif name == "names":
			self.names = []
			for element in content:
				if isinstance(element, tuple):
					feature = FeatureName()
					self.names.append(feature)
					name, attrs, content = element
					feature.fromXML(name, attrs, content, ttFont)
