#FLM: RoboFab Intro, Start here!

#
#
#	demo of starting up RoboFab
#
#

import robofab

# run this script (or 'macro' as FontLab calls them)
# if it doesn't complain, you're good to go.
#
# If you get an "ImportError" it means that python
# can't find the RoboFab module and that there is 
# probably something wrong with the way you
# installed the package.

from robofab.world import world
print world

# This should print something to the "Output" window.
# It should tell you something about the environment
# Robofab thinks it is in.
