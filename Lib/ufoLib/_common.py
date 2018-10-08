"""Private support methods shared by UFOReader, UFOWriter or glifLib.GlyphSet.
"""
from __future__ import absolute_import, unicode_literals
from ufoLib import plistlib
from ufoLib.errors import UFOLibError
import fs.errors
from datetime import datetime


if hasattr(datetime, "timestamp"):  # python >= 3.3

	def _timestamp(dt):
		return dt.timestamp()

else:
	from datetime import tzinfo, timedelta

	ZERO = timedelta(0)

	class UTC(tzinfo):

		def utcoffset(self, dt):
			return ZERO

		def tzname(self, dt):
			return "UTC"

		def dst(self, dt):
			return ZERO

	utc = UTC()

	EPOCH = datetime.fromtimestamp(0, tz=utc)

	def _timestamp(dt):
		return (dt - EPOCH).total_seconds()


def getFileModificationTime(self, path):
	"""
	Returns the modification time for the file at the given path, as a
	floating point number giving the number of seconds since the epoch.
	The path must be relative to the UFO path.
	Returns None if the file does not exist.
	"""
	try:
		dt = self.fs.getinfo(path, namespaces=["details"]).modified
	except (fs.errors.MissingInfoNamespace, fs.errors.ResourceNotFound):
		return None
	else:
		return _timestamp(dt)


def readBytesFromPath(self, path):
	"""
	Returns the bytes in the file at the given path.
	The path must be relative to the UFO's filesystem root.
	Returns None if the file does not exist.
	"""
	try:
		return self.fs.getbytes(path)
	except fs.errors.ResourceNotFound:
		return None


def _getPlist(self, fileName, default=None):
	"""
	Read a property list relative to the UFO filesystem's root.
	Raises UFOLibError if the file is missing and default is None,
	otherwise default is returned.

	The errors that could be raised during the reading of a plist are
	unpredictable and/or too large to list, so, a blind try: except:
	is done. If an exception occurs, a UFOLibError will be raised.
	"""
	try:
		with self.fs.open(fileName, "rb") as f:
			return plistlib.load(f)
	except fs.errors.ResourceNotFound:
		if default is None:
			raise UFOLibError(
				"'%s' is missing on %s. This file is required"
				% (fileName, self.fs)
			)
		else:
			return default
	except Exception as e:
		# TODO(anthrotype): try to narrow this down a little
		raise UFOLibError(
			"'%s' could not be read on %s: %s" % (fileName, self.fs, e)
		)


_msg = (
	"'%s' could not be written on %s because "
	"the data is not properly formatted: %s"
)


def _writePlist(self, fileName, obj):
	"""
	Write a property list to a file relative to the UFO filesystem's root.

	Do this sort of atomically, making it harder to corrupt existing files,
	for example when plistlib encounters an error halfway during write.
	This also checks to see if text matches the text that is already in the
	file at path. If so, the file is not rewritten so that the modification
	date is preserved.

	The errors that could be raised during the writing of a plist are
	unpredictable and/or too large to list, so, a blind try: except: is done.
	If an exception occurs, a UFOLibError will be raised.
	"""
	if self._havePreviousFile:
		try:
			data = plistlib.dumps(obj)
		except Exception as e:
			raise UFOLibError(_msg % (fileName, self.fs, e))
		if self.fs.exists(fileName) and data == self.fs.getbytes(fileName):
			return
		self.fs.setbytes(fileName, data)
	else:
		with self.fs.openbin(fileName, mode="w") as fp:
			try:
				plistlib.dump(obj, fp)
			except Exception as e:
				raise UFOLibError(_msg % (fileName, self.fs, e))
