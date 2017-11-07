import os
import sys
import shutil
from io import StringIO, BytesIO, open
import zipfile
from fontTools.misc.py23 import tounicode

haveFS = False
try:
	import fs
	from fs.osfs import OSFS
	from fs.zipfs import ZipFS
	haveFS = True
except ImportError:
	pass

from ufoLib.plistlib import readPlist, writePlist
from ufoLib.errors import UFOLibError

try:
	basestring
except NameError:
	basestring = str

_SYS_FS_ENCODING = sys.getfilesystemencoding()


def sniffFileStructure(path):
	if zipfile.is_zipfile(path):
		return "zip"
	elif os.path.isdir(path):
		return "package"
	raise UFOLibError("The specified UFO does not have a known structure.")


class FileSystem(object):

	def __init__(self, path, mode="r", structure=None):
		"""
		path can be a path or another FileSystem object.

		mode can be r or w.

		structure is only applicable in "w" mode. Options:
		None: existing structure
		package: package structure
		zip: zipped package

		mode and structure are both ignored if a FileSystem
		object is given for path.
		"""
		self._root = None
		if isinstance(path, basestring):
			path = tounicode(path, encoding=_SYS_FS_ENCODING)
			self._path = path
			if mode == "w":
				if os.path.exists(path):
					existingStructure = sniffFileStructure(path)
					if structure is not None:
						if structure != existingStructure:
							raise UFOLibError("A UFO with a different structure already exists at the given path.")
					else:
						structure = existingStructure
			elif mode == "r":
				if not os.path.exists(path):
					raise UFOLibError("The specified UFO doesn't exist: %r" % path)
				structure = sniffFileStructure(path)
			if structure == "package":
				if mode == "w" and not os.path.exists(path):
					os.mkdir(path)
				path = OSFS(path)
			elif structure == "zip":
				if not haveFS:
					raise UFOLibError("The fs module is required for reading and writing UFO ZIP.")
				path = ZipFS(
					path, write=True if mode == 'w' else False, encoding="utf8")
				roots = [
					p for p in path.listdir(u"")
					# exclude macOS metadata contained in zip file
					if path.isdir(p) and p != "__MACOSX"
				]
				if not roots:
					self._root = u"contents"
					path.makedir(self._root)
				elif len(roots) > 1:
					raise UFOLibError("The UFO contains more than one root.")
				else:
					self._root = roots[0]
		elif isinstance(path, self.__class__):
			self._root = path._root
			self._path = path._path
			path = path._fs
		else:
			raise TypeError(path)
		self._fs = path

	def close(self):
		self._fsClose()

	# --------
	# fs Calls
	# --------

	"""
	All actual low-level file system interaction
	MUST be done through these methods.

	This is necessary because ZIPs will have a
	top level root directory that packages will
	not have.
	"""

	def _fsRootPath(self, path):
		path = tounicode(path, encoding=_SYS_FS_ENCODING)
		if self._root is None:
			return path
		return self.joinPath(self._root, path)

	def _fsUnRootPath(self, path):
		if self._root is None:
			return path
		return self.relativePath(path, self._root)

	def _fsClose(self):
		self._fs.close()

	def _fsOpen(self, path, mode="r", encoding=None):
		path = self._fsRootPath(path)
		f = self._fs.open(path, mode, encoding=encoding)
		return f

	def _fsRemove(self, path):
		path = self._fsRootPath(path)
		self._fs.remove(path)

	def _fsMakeDirectory(self, path):
		path = self._fsRootPath(path)
		self._fs.makedir(path)

	def _fsRemoveTree(self, path):
		path = self._fsRootPath(path)
		self._fs.removetree(path)

	def _fsMove(self, path1, path2):
		path1 = self._fsRootPath(path1)
		path2 = self._fsRootPath(path2)
		if self.isDirectory(path1):
			self._fs.movedir(path1, path2, create=True)
		else:
			self._fs.move(path1, path2)

	def _fsExists(self, path):
		path = self._fsRootPath(path)
		return self._fs.exists(path)

	def _fsIsDirectory(self, path):
		path = self._fsRootPath(path)
		return self._fs.isdir(path)

	def _fsListDirectory(self, path):
		path = self._fsRootPath(path)
		return self._fs.listdir(path)

	def _fsGetFileModificationTime(self, path):
		path = self._fsRootPath(path)
		info = self._fs.getinfo(path, namespaces=["details"])
		return info.modified

	# -----------------
	# Path Manipulation
	# -----------------

	def joinPath(self, *parts):
		if haveFS:
			return fs.path.join(*parts)
		else:
			return os.path.join(*parts)

	def splitPath(self, path):
		if haveFS:
			return fs.path.split(path)
		else:
			return os.path.split(path)

	def directoryName(self, path):
		if haveFS:
			return fs.path.dirname(path)
		else:
			return os.path.dirname(path)

	def relativePath(self, path, start):
		if haveFS:
			return fs.relativefrom(path, start)
		else:
			return os.path.relpath(path, start)

	# ---------
	# Existence
	# ---------

	def exists(self, path):
		return self._fsExists(path)

	def isDirectory(self, path):
		return self._fsIsDirectory(path)

	def listDirectory(self, path, recurse=False):
		return self._listDirectory(path, recurse=recurse, relativeTo=path)

	def _listDirectory(self, path, recurse=False, relativeTo=None, depth=0, maxDepth=100):
		sep = os.sep
		if not relativeTo.endswith(sep):
			relativeTo += sep
		if depth > maxDepth:
			raise UFOLibError("Maximum recusion depth reached.")
		result = []
		for fileName in self._fsListDirectory(path):
			p = self.joinPath(path, fileName)
			if self.isDirectory(p) and recurse:
				result += self._listDirectory(p, recurse=True, relativeTo=relativeTo, depth=depth+1, maxDepth=maxDepth)
			else:
				p = p[len(relativeTo):]
				if sep != "/":
					# replace '\\' with '/'
					p = p.replace(sep, "/")
				result.append(p)
		return result

	def makeDirectory(self, path):
		if not self.exists(path):
			self._fsMakeDirectory(path)

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
		f = self._fsOpen(path, mode, encoding=encoding)
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
			self.makeDirectory(d)
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
		return self._fsGetFileModificationTime(path)

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
		f = self.open(path, mode="rb", encoding=encoding)
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
		self._writeFileAtomically(data, path)

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
		must be relative to the UFO.
		"""
		if not self.exists(path):
			return
		self._removeFileForPath(path, raiseErrorIfMissing=True)

	def _removeFileForPath(self, path, raiseErrorIfMissing=False):
		if not self.exists(path):
			if raiseErrorIfMissing:
				raise UFOLibError("The file %s does not exist." % path)
		else:
			if self.isDirectory(path):
				self._fsRemoveTree(path)
			else:
				self._fsRemove(path)
		directory = self.directoryName(path)
		if directory:
			self._removeEmptyDirectoriesForPath(directory)

	def _removeEmptyDirectoriesForPath(self, directory):
		if not self.exists(directory):
			return
		if not len(self._fsListDirectory(directory)):
			self._fsRemoveTree(directory)
		else:
			return
		directory = self.directoryName(directory)
		if directory:
			self._removeEmptyDirectoriesForPath(directory)

	# ----
	# Move
	# ----

	def move(self, path1, path2):
		if not self.exists(path1):
			raise UFOLibError("%s does not exist." % path1)
		if self.exists(path2):
			raise UFOLibError("%s already exists." % path2)
		self._fsMove(path1, path2)

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
		except Exception as e:
			raise UFOLibError("The file %s could not be read: %s" % (path, str(e)))

	def writePlist(self, path, obj):
		"""
		Write a property list.

		Do this sort of atomically, making it harder to
		cause corrupt files, for example when writePlist
		encounters an error halfway during write. This
		also checks to see if text matches the text that
		is already in the file at path. If so, the file
		is not rewritten so that the modification date
		is preserved.

		The errors that could be raised during the writing
		of a plist are unpredictable and/or too large to list,
		so, a blind try: except: is done. If an exception occurs,
		a UFOLibError will be raised.
		"""
		try:
			f = BytesIO()
			writePlist(obj, f)
			data = f.getvalue()
		except:
			raise UFOLibError("The data for the file %s could not be written because it is not properly formatted." % path)
		self.writeBytesToPath(path, data)


class _NOFS(object):

	def __init__(self, path):
		self._path = path

	def _absPath(self, path):
		return os.path.join(self._path, path)

	def close(self):
		pass

	def open(self, path, mode, encoding=None):
		path = self._absPath(path)
		return open(path, mode=mode, encoding=encoding)

	def remove(self, path):
		path = self._absPath(path)
		os.remove(path)

	def makedir(self, path):
		path = self._absPath(path)
		os.mkdir(path)

	def removetree(self, path):
		path = self._absPath(path)
		shutil.rmtree(path)

	def move(self, path1, path2):
		path1 = self._absPath(path1)
		path2 = self._absPath(path2)
		os.move(path1, path2)

	def movedir(self, path1, path2, create=False):
		path1 = self._absPath(path1)
		path2 = self._absPath(path2)
		exists = False
		if not create:
			if not os.path.exists(path2):
				raise UFOLibError("%r not found" % path2)
			elif not os.path.isdir(path2):
				raise UFOLibError("%r should be a directory" % path2)
			else:
				exists = True
		else:
			if os.path.exists(path2):
				if not os.path.isdir(path2):
					raise UFOLibError("%r should be a directory" % path2)
				else:
					exists = True
		if exists:
			# if destination is an existing directory, shutil.move then moves
			# the source directory inside that directory; in pyfilesytem2,
			# movedir only moves the content between the src and dst folders.
			# Here we use distutils' copy_tree instead of shutil.copytree, as
			# the latter does not work if destination exists
			from distutils.dir_util import copy_tree
			copy_tree(path1, path2)
			shutil.rmtree(path1)
		else:
			# shutil.move creates destination if not exists yet
			shutil.move(path1, path2)

	def exists(self, path):
		path = self._absPath(path)
		return os.path.exists(path)

	def isdir(self, path):
		path = self._absPath(path)
		return os.path.isdir(path)

	def listdir(self, path):
		path = self._absPath(path)
		return os.listdir(path)

	def getinfo(self, path, namespaces=None):
		from fontTools.misc.py23 import SimpleNamespace
		path = self._absPath(path)
		stat = os.stat(path)
		info = SimpleNamespace(
			modified=stat.st_mtime
		)
		return info


if not haveFS:
	OSFS = _NOFS
