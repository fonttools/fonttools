#FLM: Start FontLab remote

# On MacOS this will make FontLab accept apple events.
# It will assume the event contains a piece of executable
# python code and run it. The results of the python code
# are then returned in the reply.
#
# Check the code in robofab/tools/remote.py for more 
# functionality. For instance, it contains several
# functions to send and receive glyphs from outside
# FontLab, offering a way to make your NoneLab Python
# scripts communicate with FontLab.

from robofab.tools.remote import *

