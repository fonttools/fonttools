"""fontTools.misc.binTools.py -- tools for binary manipulation of integers
"""


def testBit(int_type, offset):
  """Return True if the bit at 'offset' is one."""
  mask = 1 << offset
  return bool(int_type & mask)


def setBit(int_type, offset):
  """Return an integer with the bit at 'offset' set to 1."""
  mask = 1 << offset
  return int_type | mask


def clearBit(int_type, offset):
  """Return an integer with the bit at 'offset' set to 0."""
  mask = ~(1 << offset)
  return int_type & mask


def toggleBit(int_type, offset):
  """Return an integer with the bit at 'offset' inverted: 0 -> 1 and 1 -> 0."""
  mask = 1 << offset
  return int_type ^ mask


def getBitRange(int_type, start, end):
  """Slice and return an integer's bit mask from 'start' to 'end'."""
  mask = 2**(end - start) - 1
  return (int_type >> start) & mask


def setBitRange(int_type, start, end, value):
  """Set an integer's bit mask between 'start' and 'end' to 'value'."""
  mask = 2**(end - start) - 1
  value = (value & mask) << start
  mask = mask << start
  return (int_type & ~mask) | value
