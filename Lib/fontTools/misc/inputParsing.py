import unicodedata
import urllib2
import codecs
from urllib2 import urlopen
from bs4 import BeautifulSoup


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

def getCharListFromInput(input, encoding):
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

