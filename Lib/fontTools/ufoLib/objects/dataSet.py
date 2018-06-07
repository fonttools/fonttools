from fontTools.ufoLib.objects.misc import DataStore
from fontTools.ufoLib.reader import UFOReader
from fontTools.ufoLib.writer import UFOWriter


class DataSet(DataStore):
    readf = UFOReader.readData
    writef = UFOWriter.writeData
    deletef = UFOWriter.deleteData
