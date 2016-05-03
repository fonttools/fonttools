import os
from io import StringIO
from fs.osfs import OSFS
from fs.zipfs import ZipFS, ZipOpenError
from ufoLib.plistlibShim import readPlist, writePlist
from ufoLib.errors import UFOLibError

try:
	basestring
except NameError:
	basestring = str


class FileSystem(object):

	def __init__(self, path):
		self._path = "<data stream>"
		if isinstance(path, basestring):
			self._path = path
			if not os.path.exists(path):
				raise UFOLibError("The specified UFO doesn't exist.")
			if os.path.isdir(path):
				path = OSFS(path)
			else:
				try:
					path = ZipFS(path, mode="r", allow_zip_64=True)
				except ZipOpenError:
					raise UFOLibError("The specified UFO is not in a proper format.")
		self._fs = path

	def close(self):
		self._fs.close()

	# -----------------
	# Path Manipulation
	# -----------------

	def joinPath(self, *parts):
		return os.path.join(*parts)

	def splitPath(self, path):
		return os.path.split(path)

	def directoryName(self, path):
		return self.splitPath(path)[0]

	def relativePath(self, path, start):
		return os.path.relpath(path, start)

	# ---------
	# Existence
	# ---------

	def exists(self, path):
		return self._fs.exists(path)

	def isDirectory(self, path):
		return self._fs.isdir(path)

	def listDirectory(self, path, recurse=False):
		return self._listDirectory(path, recurse=recurse)

	def _listDirectory(self, path, recurse=False, depth=0, maxDepth=100):
		if depth > maxDepth:
			raise UFOLibError("Maximum recusion depth reached.")
		result = []
		for fileName in self._fs.listdir(path):
			p = self.joinPath(path, fileName)
			if os.path.isdir(p) and recurse:
				result += self._listDirectory(p, recurse=True, depth=depth+1, maxDepth=maxDepth)
			else:
				result.append(p)
		return result

	# -----------
	# File Opener
	# -----------

	def open(self, path, mode="r", encoding=None):
		"""
		Returns a file (or file-like) object for the
		file at the given path. The path must be relative
		to the UFO path. Returns None if the file does
		not exist and the mode is "r" or "rb. An encoding
		may be passed if needed.

		Note: The caller is responsible for closing the open file.
		"""
		if encoding:
			if mode == "r":
				mode = "rb"
			elif mode == "w":
				mode = "wb"
		if mode in ("r", "rb") and not self.exists(path):
			return None
		if self.exists(path) and self.isDirectory(path):
			raise UFOLibError("%s is a directory." % path)
		if mode in ("w", "wb"):
			self._buildDirectoryTree(path)
		f = self._fs.open(path, mode, encoding=encoding)
		return f

	def _buildDirectoryTree(self, path):
		directory, fileName = self.splitPath(path)
		directoryTree = []
		while directory:
			directory, d = self.splitPath(directory)
			directoryTree.append(d)
		directoryTree.reverse()
		built = ""
		for d in directoryTree:
			d = self.joinPath(built, d)
			p = self.joinPath(self._path, d)
			if not self.exists(p):
				self._fs.mkdir(p)
			built = d

	# ------------------
	# Modification Times
	# ------------------

	def getFileModificationTime(self, path):
		"""
		Returns the modification time (as reported by os.path.getmtime)
		for the file at the given path. The path must be relative to
		the UFO path. Returns None if the file does not exist.
		"""
		if not self.exists(path):
			return None
		info = self._fs.getinfo(path)
		return info["modified_time"]

	# --------------
	# Raw Read/Write
	# --------------

	def readBytesFromPath(self, path, encoding=None):
		"""
		Returns the bytes in the file at the given path.
		The path must be relative to the UFO path.
		Returns None if the file does not exist.
		An encoding may be passed if needed.
		"""
		f = self.open(path, mode="r", encoding=encoding)
		if f is None:
			return None
		data = f.read()
		f.close()
		return data

	def writeBytesToPath(self, path, data, encoding=None):
		"""
		Write bytes to path. If needed, the directory tree
		for the given path will be built. The path must be
		relative to the UFO. An encoding may be passed if needed.
		"""
		if encoding:
			data = StringIO(data).encode(encoding)
		self._writeFileAtomically(data, fullPath)

	def _writeFileAtomically(self, data, path):
		"""
		Write data into a file at path. Do this sort of atomically
		making it harder to cause corrupt files. This also checks to see
		if data matches the data that is already in the file at path.
		If so, the file is not rewritten so that the modification date
		is preserved.
		"""	
		assert isinstance(data, bytes)
		if self.exists(path):
			f = self.open(path, "rb")
			oldData = f.read()
			f.close()
			if data == oldData:
				return
		if data:
			f = self.open(path, "wb")
			f.write(data)
			f.close()

	# ------------
	# File Removal
	# ------------

	def remove(self, path):
		"""
		Remove the file (or directory) at path. The path
		must be relative to the UFO. This is only allowed
		for files in the data and image directories.
		"""
		d = path
		parts = []
		while d:
			d, p = self.splitPath(d)
			if p:
				parts.append(p)
		if parts[-1] not in ("images", "data"):
			raise UFOLibError("Removing \"%s\" is not legal." % path)
		self._removeFileForPath(path, raiseErrorIfMissing=True)

	def _removeFileForPath(self, path, raiseErrorIfMissing=False):
		if not self.exists(path):
			if raiseErrorIfMissing:
				raise UFOLibError("The file %s does not exist." % path)
		else:
			if self.isDirectory(path):
				self._fs.removedir(path)
			else:
				self._fs.remove(path)
		directory = self.directoryName(path)
		self._removeEmptyDirectoriesForPath(directory)

	def _removeEmptyDirectoriesForPath(self, directory):
		if not self.exists(directory):
			return
		if not len(self._fs.listdir(directory)):
			self._fs.removedir(directory)
		else:
			return
		directory = self.directoryName(directory)
		if directory:
			self._removeEmptyDirectoriesForPath(directory)

	# --------------
	# Property Lists
	# --------------

	def readPlist(self, path, default=None):
		"""
		Read a property list relative to the
		UFO path. If the file is missing and
		default is None a UFOLibError will be
		raised. Otherwise default is returned.
		The errors that could be raised during
		the reading of a plist are unpredictable
		and/or too large to list, so, a blind
		try: except: is done. If an exception
		occurs, a UFOLibError will be raised.
		"""
		if not self.exists(path):
			if default is not None:
				return default
			else:
				raise UFOLibError("%s is missing. This file is required" % path)
		try:
			with self.open(path, "rb") as f:
				return readPlist(f)
		except:
			raise UFOLibError("The file %s could not be read." % fileName)


if __name__ == "__main__":
	from ufoLib import UFOReader
	path = os.path.dirname(__file__)
	path = os.path.dirname(path)
	path = os.path.dirname(path)
	path = os.path.join(path, "TestData", "TestFont1 (UFO2).ufo")

	import zipfile

	def _packDirectory(z, d, root=""):
		for i in os.listdir(d):
			p = os.path.join(d, i)
			l = os.path.join(root, i)
			if os.path.isdir(p):
				_packDirectory(z, p, root=l)
			else:
				l = os.path.join(root, i)
				z.write(p, l)

	p = path + ".zip"
	if os.path.exists(p):
		os.remove(p)
	z = zipfile.ZipFile(p, "w")
	_packDirectory(z, path)
	z.close()

	path += ".zip"

	reader = UFOReader(path)
	glyphSet = reader.getGlyphSet()
	print glyphSet.getGLIF("A")
