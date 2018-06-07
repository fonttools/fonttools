from ufoLib2.objects.misc import DataStore
from ufoLib2.reader import UFOReader
from ufoLib2.writer import UFOWriter


class ImageSet(DataStore):
    readf = UFOReader.readImage
    writef = UFOWriter.writeImage
    deletef = UFOWriter.deleteImage
