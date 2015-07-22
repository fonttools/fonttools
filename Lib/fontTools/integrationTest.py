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
import unicodedata
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
    return page

def readInput(input, encoding):
    try:
        data = readFile(input, encoding)
    except IOError:
        data = readPage(input)

    soup = BeautifulSoup(data)
    texts = soup.findAll(text=True)
    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
    string = soup.getText()

    charList = list(set(string))

    #reference to unicode categories http://www.sql-und-xml.de/unicode-database/#kategorien
    non_printable = ['Zs', 'Zl', 'Zp', 'Cc']
    charList = [x for x in charList if unicodedata.category(x) not in non_printable]

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
    template = "{0:25}  {1:20}"
    print template.format("ttf: %d => %d" % (origSize, subsSize), "(Reduction of %.2f%%)" % ( (((origSize - subsSize)*100)/origSize)) )
    print template.format("ttx: %d => %d" % (ttxOrigSize, ttxSubsSize), "(Reduction of %.2f%%)" % ( ((ttxOrigSize - ttxSubsSize)*100)/ttxOrigSize) )

    origTotalSize = 0
    subsTotalSize = 0
    counting = None
    subtag = None
    countingBytecode = False 
    origTables = []    
    subsTables = []

    with open("original.ttx") as infp:
        for line in infp:
            if not line.strip():
                continue
            if(counting == None):
                if any(word in line for word in opentags):
                    counting = line[line.find("<")+1:line.find(">")]
            elif(counting == "glyf"):
                if(subtag == None):
                    if any(word in line for word in closetags):
                        counting = None
                    elif '<' in line and '/' not in line and '>' in line:
                        searchTag = line[line.find("<")+1:line.find(">")]
                        if not searchTag.startswith("TTGlyph"):
                            subtag = searchTag
                else:
                    if "</"+subtag+">" in line:
                        subtag = None
                    else:
                        origTotalSize += len(line.encode('utf-8'))
                
            else:
                if not any(word in line for word in closetags):
                    origTotalSize += len(line.encode('utf-8'))
                else:
                    counting = None
 
    with open("subsetted.ttx") as infp:
        for line in infp:
            if not line.strip():
                continue
            if(counting == None):
                if any(word in line for word in opentags):
                    counting = line[line.find("<")+1:line.find(">")]
            elif(counting == "glyf"):
                if(subtag == None):
                    if any(word in line for word in closetags):
                        counting = None
                    elif '<' in line and '/' not in line and '>' in line:
                        searchTag = line[line.find("<")+1:line.find(">")]
                        if not searchTag.startswith("TTGlyph"):
                            subtag = searchTag
                else:
                    if "</"+subtag+">" in line:
                        subtag = None
                    else:
                        subsTotalSize += len(line.encode('utf-8'))
            else:
                if not any(word in line for word in closetags):
                    subsTotalSize += len(line.encode('utf-8'))
                else:
                    counting = None
    subtag = None
    with open("original.ttx") as infp:
            for line in infp:
                if not line.strip():
                    continue
                if(counting == None):
                    if any(word in line for word in opentags):
                        size = 0
                        bytecodeSize = 0
                        tag = line[line.find("<")+1:line.find(">")]
                        counting = tag
                elif(counting == "glyf"):
                    if(subtag == None):
                        if any(word in line for word in closetags):
                            counting = None
                            bytePercent = (size*100)/origTotalSize
                            origTables.append([tag, bytePercent, size])
                            bytePercent = (bytecodeSize*100)/origTotalSize
                            if(bytecodeSize > 0):
                                origTables.append([tag+'(assemb)', bytePercent, bytecodeSize]) 
                        elif '<' in line and '/' not in line and '>' in line:
                            searchTag = line[line.find("<")+1:line.find(">")]
                            if not searchTag.startswith("TTGlyph"):
                                subtag = searchTag
                    elif(subtag == "instructions" or subtag == "assembly"):
                        if "</"+subtag+">" in line:
                            subtag = None
                        else:
                            bytecodeSize += len(line.encode('utf-8'))
                    else: 
                        if "</"+subtag+">" in line:
                            subtag = None
                        else:
                            size += len(line.encode('utf-8'))
                else:
                    if not any(word in line for word in closetags):
                        size += len(line.encode('utf-8'))
                    else:
                        counting = None
                        bytePercent = (size*100)/origTotalSize
                        origTables.append([tag, bytePercent, size])

    subtag = None
    with open("subsetted.ttx") as infp:
            for line in infp:
                if not line.strip():
                    continue
                if(counting == None):
                    if any(word in line for word in opentags):
                        size = 0
                        bytecodeSize = 0
                        tag = line[line.find("<")+1:line.find(">")]
                        counting = tag 
                elif(counting == "glyf"):
                    if(subtag == None):
                        if any(word in line for word in closetags):
                            counting = None
                            bytePercent = (size*100)/subsTotalSize
                            subsTables.append([tag, bytePercent, size])
                            bytePercent = (bytecodeSize*100)/subsTotalSize
                            if(bytecodeSize > 0):
                                subsTables.append([tag+'(assemb)', bytePercent, bytecodeSize]) 
                        elif '<' in line and '/' not in line and '>' in line:
                            searchTag = line[line.find("<")+1:line.find(">")]
                            if not searchTag.startswith("TTGlyph"):
                                subtag = searchTag
                    elif(subtag == "instructions" or subtag == "assembly"):
                        if "</"+subtag+">" in line:
                            subtag = None
                        else:
                            bytecodeSize += len(line.encode('utf-8'))
                    else: 
                        if "</"+subtag+">" in line:
                            subtag = None
                        else:
                            size += len(line.encode('utf-8'))
                else:
                    if not any(word in line for word in closetags):
                        size += len(line.encode('utf-8'))
                    else:
                        counting = None
                        bytePercent = (size*100)/subsTotalSize
                        subsTables.append([tag, bytePercent, size])
   
    origTables = sorted(origTables, reverse=True, key=lambda tup:tup[2])
    subsTables = sorted(subsTables, reverse=True, key=lambda tup:tup[2])

    print("")
    template = "{0:15} {1:12} {2:12} {3:12} {4:12} {5:12}"
    print template.format("Table", "Size", "Total%", "New Size", "Total%", "")
    
    for table in origTables:
        row = [table[0], "{:,}".format(table[2]), "{:.2f}".format(table[1])]
        
        for substable in subsTables:
            if substable[0] == table[0]:
                row.extend(["{:,}".format(substable[2]), "{:.2f}".format(substable[1])])
                
                reduction = ((table[2]-substable[2])*100)/table[2]
                if(reduction > 0):
                    row.append("(reduction of {:.2f}%)".format(reduction))
                else:
                    row.append("")
        else:
            row.extend(["---", "---", ""])
        print template.format(*row) 
    print("\n")


    os.remove("original.ttx")
    os.remove("subsetted.ttx")

def main(args):
    
    if len(args) > 0:
        with open(args[0], "r") as file:
            testSuite.clear()
            for nl, line in enumerate(file):
               try:
                    font, glyphs = line.split()
                    testSuite.add((font, glyphs, 'utf-8'))
               except:
                    font, glyphs, encoding = line.split()
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


