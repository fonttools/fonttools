from ufoLib2.objects.misc import DataStore
from ufoLib2.reader import UFOReader
from ufoLib2.writer import UFOWriter


class DataSet(DataStore):
    readf = UFOReader.readData
    writef = UFOWriter.writeData
    deletef = UFOWriter.deleteData
