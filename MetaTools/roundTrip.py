#! /usr/bin/env python

"""usage: ttroundtrip [options] font1 ... fontN

    Dump each TT/OT font as a TTX file, compile again to TTF or OTF
    and dump again. Then do a diff on the two TTX files. Append problems
    and diffs to a file called "report.txt" in the current directory.
    This is only for testing FontTools/TTX, the resulting files are
    deleted afterwards.

    This tool supports some of ttx's command line options (-i, -t
    and -x). Specifying -t or -x implies ttx -m <originalfile> on
    the way back.
"""


import sys
import os
import tempfile
import getopt
import traceback
from fontTools import ttx

class Error(Exception): pass


def usage():
	print(__doc__)
	sys.exit(2)


def roundTrip(ttFile1, options, report):
	fn = os.path.basename(ttFile1)
	xmlFile1 = tempfile.mktemp(".%s.ttx1" % fn)
	ttFile2 = tempfile.mktemp(".%s" % fn)
	xmlFile2 = tempfile.mktemp(".%s.ttx2" % fn)
	
	try:
		ttx.ttDump(ttFile1, xmlFile1, options)
		if options.onlyTables or options.skipTables:
			options.mergeFile = ttFile1
		ttx.ttCompile(xmlFile1, ttFile2, options)
		options.mergeFile = None
		ttx.ttDump(ttFile2, xmlFile2, options)
		
		diffcmd = 'diff -U2 -I ".*modified value\|checkSumAdjustment.*" "%s" "%s"' % (xmlFile1, xmlFile2)
		output = os.popen(diffcmd, "r", 1)
		lines = []
		while True:
			line = output.readline()
			if not line:
				break
			sys.stdout.write(line)
			lines.append(line)
		if lines:
			report.write("=============================================================\n")
			report.write("  \"%s\" differs after round tripping\n" % ttFile1)
			report.write("-------------------------------------------------------------\n")
			report.writelines(lines)
		else:
			print("(TTX files are the same)")
	finally:
		for tmpFile in (xmlFile1, ttFile2, xmlFile2):
			if os.path.exists(tmpFile):
				os.remove(tmpFile)


def main(args):
	try:
		rawOptions, files = getopt.getopt(args, "it:x:")
	except getopt.GetoptError:
		usage()
	
	if not files:
		usage()
	
	with open("report.txt", "a+") as report:
		options = ttx.Options(rawOptions, len(files))
		for ttFile in files:
			try:
				roundTrip(ttFile, options, report)
			except KeyboardInterrupt:
				print("(Cancelled)")
				break
			except:
				print("*** round tripping aborted ***")
				traceback.print_exc()
				report.write("=============================================================\n")
				report.write("  An exception occurred while round tripping")
				report.write("  \"%s\"\n" % ttFile)
				traceback.print_exc(file=report)
				report.write("-------------------------------------------------------------\n")

	
main(sys.argv[1:])
