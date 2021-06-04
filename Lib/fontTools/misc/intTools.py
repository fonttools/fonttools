__all__ = ['popCount']


try:
    bit_count = int.bit_count
except AttributeError:
    def bit_count(v):
        return bin(v).count('1')

"""Return number of 1 bits (population count) of the absolute value of an integer.

See https://docs.python.org/3.10/library/stdtypes.html#int.bit_count
"""
popCount = bit_count
