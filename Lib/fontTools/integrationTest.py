#! /usr/bin/env python

from __future__ import division
import sys
import getopt
import codecs
import re 
import urllib2
import logging
import os
import subset
import compare
from misc.captureOutput import captureOutput
from fontTools.ttLib import TTFont
from bs4 import BeautifulSoup
from os import rename, listdir
from urllib2 import urlopen
from cStringIO import StringIO

testSuite = { ('NotoSans-Regular.ttf', 'http://www.gutenberg.org/files/2554/2554-h/2554-h.htm', 'utf-8'),
              ('NotoSans-Regular.ttf', 'http://az.lib.ru/d/dostoewskij_f_m/text_0060.shtml', 'utf-8'),  
              ('NotoSans-Regular.ttf', 'https://uwaterloo.ca/', 'utf-8'),
              ('NotoSansHebrew-Regular.ttf', 'http://benyehuda.org/brenner/crime.html', 'utf-8') }

tables = ["acnt", "ankr", "avar", "bdat", "bhed", "bloc", "bsln", "cmap", 
            "cvar", "cvt", "EBSC", "fdsc", "feat", "fmtx", "fond", "fpgm", 
            "fvar", "gasp", "glyf", "gvar", "hdmx", "head", "hhea", "hmtx", 
            "just", "kern", "kerx", "lcar", "loca", "ltag", "maxp", "meta", 
            "mort", "morx", "name", "opbd", "OS_2", "post", "prep", "prop",
            "sbix", "trak", "vhea", "vmtx", "xref", "Zapf","GlyphOrder", 
            "GDEF", "GPOS", "GSUB"]

opentags = [ '<'+x+'>' for x in tables ]
closetags = [ '</'+x+'>' for x in tables ]

def ttDump(input, output):
    ttf = TTFont(input, 0, verbose=False, allowVID=False, quiet=False, 
            ignoreDecompileErrors=True, fontNumber=-1)
    ttf.saveXML(output, quiet=True, tables= [], skipTables= [], 
            splitTables=False, disassembleInstructions=True,
            bitmapGlyphDataFormat='raw')
    ttf.close()

def makeOutputFileName(input, extension):
    dirName, fileName = os.path.split(input)
    fileName, ext = os.path.splitext(fileName)
    output = os.path.join(dirName, fileName + extension)
    n = 1
    while os.path.exists(output):
        output = os.path.join(dirName, fileName + "#" + repr(n) + extension)
        n = n + 1
    return output

def readFile(input, encoding):
    try:
        with codecs.open(input) as file:
            data=file.read()
    except:
        raise IOError("Couldn't open file "+input)

    try:
        data = data.decode(encoding)
    except:
        raise ValueError("Different encoding or wrong code provided: "+encoding)
    return data 

def readPage(input):
    #some sites block common non-browser user agent strings, better use a regular one
    hdr = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
    request = urllib2.Request(input, headers = hdr)
    try:
        page = urllib2.urlopen(request)
    except:
        raise ValueError("Couldn't load file or URL "+input)
    soup = BeautifulSoup(page)
    texts = soup.findAll(text=True)
    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
    visible_text = soup.getText()
    return visible_text

def readInput(input, encoding):
    try:
        string = readFile(input, encoding)
    except IOError:
        string = readPage(input)

    charList = list(set(string))

    escapeList = ['\n', '\t', '\v', '\r', '\f', '\b', '\a']
    charList = [x for x in charList if x not in escapeList]
    return charList


def listToStr(charList):
    string = ''
    for char in charList:
        string += char
    return string

def makeArgs(*params):
    args = []
    for param in params:
        args.append(param)
    return args
 
def usage():
    print("usage: pyftpageSubset [options] fontFile inputFile")
    sys.exit(2)

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "e:s")
    except getopt.GetoptError:
        usage()

    encoding = 'utf-8'
    showStats = False
    if not files or len(files) != 2:
        usage()
    else:
        fontFile = files[0]
        inputFile = files[1]

    for option, value in rawOptions:
        if option == "-e":
            encoding = value
        if option == "-s":
            showStats = True

    return fontFile, inputFile, encoding, showStats

def parseOutput(output):
    lines = output.split('\n')
    for n, line in enumerate(lines):
        if "Testing at " in line:
            print(line[11:]),
            aNotFound, bNotFound = lines[n+3][28:].split('-')
            if lines[n+2][-2:] != " 0" or aNotFound != bNotFound:
                print(" FAILED")
                if lines[n+3][-2:] != " 0":
                    print(lines[n+2])
                if aNotFound != bNotFound:
                    print("Glyphs missing in original/subsetted font: %s/%s" % (aNotFound, bNotFound)) 
            else:
                print(" PASSED")
            
def performAnalysis(fontFile, subsetFontFile):

    print("\n"+fontFile+" Analysis")
    ttDump(fontFile, "original.ttx")
    ttDump(subsetFontFile, "subsetted.ttx")
   
    currentDir = os.getcwd() 
    origSize = os.path.getsize(currentDir+"/"+fontFile)
    subsSize = os.path.getsize(currentDir+"/"+subsetFontFile)

    ttxOrigSize = os.path.getsize(currentDir+"/original.ttx")
    ttxSubsSize = os.path.getsize(currentDir+"/subsetted.ttx")

    print("New size: " )
    print("ttf: %d => %d" % (origSize, subsSize) +"\tttx: %d => %d" % (ttxOrigSize, ttxSubsSize))
    print("Reduction of %.2f%%" % ( (((origSize - subsSize)*100)/origSize)) +"\t\tReduction of %.2f%%" % (  ((ttxOrigSize - ttxSubsSize)*100)/ttxOrigSize) )

    origTotalSize = 0
    subsTotalSize = 0
    counting = False
    origTables = []    
    subsTables = []

    with open("original.ttx") as infp:
        for line in infp:
            if not line.strip():
                continue
            if(counting == False):
                if any(word in line for word in opentags):
                    counting = True
            else:
                if not any(word in line for word in closetags):
                    origTotalSize += len(line.encode('utf-8'))
                else:
                    counting = False
    
    with open("subsetted.ttx") as infp:
        for line in infp:
            if not line.strip():
                continue
            if(counting == False):
                if any(word in line for word in opentags):
                    counting = True
            else:
                if not any(word in line for word in closetags):
                    subsTotalSize += len(line.encode('utf-8'))
                else:
                    counting = False
    
    with open("original.ttx") as infp:
            for line in infp:
                if not line.strip():
                    continue
                if(counting == False):
                    if any(word in line for word in opentags):
                        size = 0
                        counting = True
                        tag = line[line.find("<")+1:line.find(">")]

                else:
                    if not any(word in line for word in closetags):
                        size += len(line.encode('utf-8'))
                    else:
                        counting = False
                        bytePercent = (size*100)/origTotalSize
                        origTables.append([tag, bytePercent, size])

    with open("subsetted.ttx") as infp:
            for line in infp:
                if not line.strip():
                    continue
                if(counting == False):
                    if any(word in line for word in opentags):
                        size = 0
                        counting = True
                        tag = line[line.find("<")+1:line.find(">")]

                else:
                    if not any(word in line for word in closetags):
                        size += len(line.encode('utf-8'))
                    else:
                        counting = False
                        bytePercent = (size*100)/subsTotalSize
                        subsTables.append([tag, bytePercent, size])
   
    origTables = sorted(origTables, reverse=True, key=lambda tup:tup[2])
    subsTables = sorted(subsTables, reverse=True, key=lambda tup:tup[2])
 
    print("\n")
    print(fontFile+"\t\t \t=>\t\t"+subsetFontFile)
    print("Table\t\tTotal%\t\tSize\t\t=>\t\tTable\t\tTotal%\t\tSize")
    print("Total\t\t100%%\t\t%d\t\t\t\tTotal\t\t100%%\t\t%d" % (origTotalSize, subsTotalSize))
    for table in origTables:
        print("%s \t\t%.2f\t\t%d\t\t  " % (table[0][:6], table[1], table[2])),
        for substable in subsTables:
            if substable[0] == table[0]:
                print("\t\t%s \t\t%.2f\t\t%d" % (substable[0][:6], substable[1], substable[2])),
                reduction = ((table[2]-substable[2])*100)/table[2]
                if (reduction >= 1):
                    print("\t (reduction of %0.f%%)" % reduction)
                else:
                    print("")
                break
    print("\n")               


def main(args):
    
    if len(args) > 0:
        with open(args[0], "r") as file:
            testSuite.clear()
            for nl, line in enumerate(file):
               try:
                    font, glyphs = line.split()
                    testSuite.add((font, glyphs, 'utf-8'))
               except:
                    font, glyphs, encoding, stats = line.split()
                    testSuite.add((font, glyphs, encoding))

    for fontFile, inputFile, encoding in testSuite:
    
        print("Testing "+fontFile+" over "+inputFile)        
        charList = readInput(inputFile, encoding)
        glyphs = "--text="+listToStr(charList)
 
        filesBefore = listdir(".")   
        args = makeArgs(fontFile, glyphs, '-f')
        with captureOutput():
            subset.main(args)
        filesAfter = listdir(".") 
 
        #tries to identifiy a new file created in the current folder
        #if fail, assumes that a file with the same name was already there 
        try:   
            createdFile = [item for item in filesAfter if item not in filesBefore][0] 
        except:
            createdFile = fontFile+'.subset'
         
        subsetFontFile = makeOutputFileName('Subset'+fontFile, '.ttf')
        rename(createdFile, subsetFontFile)

        args = makeArgs(fontFile, subsetFontFile, inputFile)
        with captureOutput() as capture:
            compare.main(args)
            output = capture.getOutput()

        parseOutput(output)
        performAnalysis(fontFile, subsetFontFile)


if __name__ == '__main__':
  main(sys.argv[1:])


