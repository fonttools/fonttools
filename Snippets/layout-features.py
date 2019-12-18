#! /usr/bin/env python3

from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
import sys

if len(sys.argv) != 2:
	print("usage: layout-features.py fontfile.ttf")
	sys.exit(1)
fontfile = sys.argv[1]
if fontfile.rsplit(".", 1)[-1] == "ttx":
	font = TTFont()
	font.importXML(fontfile)
else:
	font = TTFont(fontfile)

for tag in ('GSUB', 'GPOS'):
	if not tag in font: continue
	print("Table:", tag)
	table = font[tag].table
	if not table.ScriptList or not table.FeatureList: continue
	featureRecords = table.FeatureList.FeatureRecord
	for script in table.ScriptList.ScriptRecord:
		print("  Script:", script.ScriptTag)
		if not script.Script:
			print ("    Null script.")
			continue
		languages = list(script.Script.LangSysRecord)
		if script.Script.DefaultLangSys:
			defaultlangsys = otTables.LangSysRecord()
			defaultlangsys.LangSysTag = "default"
			defaultlangsys.LangSys = script.Script.DefaultLangSys
			languages.insert(0, defaultlangsys)
		for langsys in languages:
			print("    Language:", langsys.LangSysTag)
			if not langsys.LangSys:
				print ("    Null language.")
				continue
			features = [featureRecords[index] for index in langsys.LangSys.FeatureIndex]
			if langsys.LangSys.ReqFeatureIndex != 0xFFFF:
				record = featureRecords[langsys.LangSys.ReqFeatureIndex]
				requiredfeature = otTables.FeatureRecord()
				requiredfeature.FeatureTag = 'required(%s)' % record.FeatureTag
				requiredfeature.Feature = record.Feature
				features.insert(0, requiredfeature)
			for feature in features:
				print("      Feature:", feature.FeatureTag)
				lookups = feature.Feature.LookupListIndex
				print("        Lookups:", ','.join(str(l) for l in lookups))
