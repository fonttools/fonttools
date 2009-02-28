"""
ROBOFAB
RoboFab is a Python library with objects
that deal with data usually associated
with fonts and type design.

DEVELOPERS
RoboFab is developed and maintained by
	Tal Leming
	Erik van Blokland
	Just van Rossum
	(in no particular order)

MORE INFO
The RoboFab homepage, documentation etc.
http://robofab.com

LICENSE
Some restrictions apply.
http://robofab.com/download/index.html

HISTORY
RoboFab starts somewhere during the 
TypoTechnica in Heidelberg, 2003.

COPYRIGHT
The package is copyrighted by the RoboFab
developers and can only be used with the 
express permission of the developers.

DISCLAIMER
This code is under construction. Make backup
copies of your work before using code from 
RoboFab. The RoboFab developers won't accept
any responsibility for loss of data, damaged
work, or problems of any kind caused by
operating RoboFab or the inability to use
parts of or the entire module. Etcetera.
RoboFab is not time sensitive. Don't use RoboFab
in Nuclear powerstations or airtraffic control
software.

DEPENDENCIES
RoboFab expects fontTools to be installed.
http://sourceforge.net/projects/fonttools/
Some of the RoboFab modules require data files
that are included in the source directory.
RoboFab likes to be able to calculate paths 
to these data files all by itself, so keep them
together with the source files.

QUOTES
Yuri Yarmola:
"If data is somehow available to other programs
via some standard data-exchange interface which
can be accessed by some library in Python, you
can make a Python script that uses that library
to apply data to a font opened in FontLab."

W.A. Dwiggins:
"You will understand that I am not trying to
short-circuit any of your shop operations in
sending drawings of this kind. The closer I can
get to the machine the better the result.
Subtleties of curves are important, as you know,
and if I can make drawings that can be used in
the large size I have got one step closer to the
machine that cuts the punches." [1932]

"""


class RoboFabError(Exception): pass

class RoboFabWarning(Warning): pass


numberVersion = (1, 2, "develop", 0)
version = "1.2.0d"
