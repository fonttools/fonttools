from fontTools.ufoLib.objects.misc import DataStore
from fontTools.ufoLib.reader import UFOReader
from fontTools.ufoLib.writer import UFOWriter


class ImageSet(DataStore):
    readf = UFOReader.readImage
    writef = UFOWriter.writeImage
    deletef = UFOWriter.deleteImage
