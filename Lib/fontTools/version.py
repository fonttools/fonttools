try:
	__version__ = __import__('pkg_resources').require('fontTools')[0].version
except Exception:
	__version__ = 'unknown'
