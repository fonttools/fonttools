#! /usr/bin/env python

import sys
import getopt
import codecs
import re 
import urllib2
import logging
import os
import subset
import compare
from bs4 import BeautifulSoup
from os import rename, listdir
from urllib2 import urlopen
from cStringIO import StringIO

testSuite = { ('NotoSans-Regular.ttf', 'http://www.gutenberg.org/files/2554/2554-h/2554-h.htm', 'utf-8'),
              ('NotoSans-Regular.ttf', 'http://az.lib.ru/d/dostoewskij_f_m/text_0060.shtml', 'utf-8'),  
              ('NotoSans-Regular.ttf', 'https://uwaterloo.ca/', 'utf-8'),
              ('NotoSansHebrew-Regular.ttf', 'http://benyehuda.org/brenner/crime.html', 'utf-8') }

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
        rawOptions, files = getopt.getopt(args, "e:")
    except getopt.GetoptError:
        usage()

    encoding = 'utf-8'
    if not files or len(files) != 2:
        usage()
    else:
        fontFile = files[0]
        inputFile = files[1]

    for option, value in rawOptions:
        if option == "-e":
            encoding = value

    return fontFile, inputFile, encoding

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
            

def main(args):
    #fontFile, inputFile, encoding = parseOptions(args)
    
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
        args = makeArgs(fontFile, glyphs)
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

        #capture stdout
        backup = sys.stdout
        sys.stdout = StringIO()

        args = makeArgs(fontFile, subsetFontFile, inputFile)
        compare.main(args)

        output = sys.stdout.getvalue()
        #restore stdout
        sys.stdout.close()   
        sys.stdout = backup 
        #os.remove(subsetFontFile)        

        parseOutput(output)
        #print(output)

if __name__ == '__main__':
  main(sys.argv[1:])
