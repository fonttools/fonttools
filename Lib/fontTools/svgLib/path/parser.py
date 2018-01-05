# SVG Path specification parser.
# This is an adaptation from 'svg.path' by Lennart Regebro (@regebro),
# modified so that the parser takes a FontTools Pen object instead of
# returning a list of svg.path Path objects.
# The original code can be found at:
# https://github.com/regebro/svg.path/blob/4f9b6e3/src/svg/path/parser.py
# Copyright (c) 2013-2014 Lennart Regebro
# License: MIT

from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from fontTools.misc.py23 import *
from math import sqrt, cos, sin, acos, degrees, radians
import re

COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
UPPERCASE = set('MZLHVCSQTA')

COMMAND_RE = re.compile("([MmZzLlHhVvCcSsQqTtAa])")
FLOAT_RE = re.compile("[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")

class Arc(object):

    def __init__(self, start, radius, rotation, arc, sweep, end):
        """radius is complex, rotation is in degrees,
           arc and sweep are 1 or 0 (True/False also work)"""

        self.start = start
        self.radius = radius
        self.rotation = rotation
        self.arc = bool(arc)
        self.sweep = bool(sweep)
        self.end = end

        self._parameterize()

    def _parameterize(self):
        # Conversion from endpoint to center parameterization
        # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

        cosr = cos(radians(self.rotation))
        sinr = sin(radians(self.rotation))
        dx = (self.start.real - self.end.real) / 2
        dy = (self.start.imag - self.end.imag) / 2
        x1prim = cosr * dx + sinr * dy
        x1prim_sq = x1prim * x1prim
        y1prim = -sinr * dx + cosr * dy
        y1prim_sq = y1prim * y1prim

        rx = self.radius.real
        rx_sq = rx * rx
        ry = self.radius.imag
        ry_sq = ry * ry

        # Correct out of range radii
        radius_check = (x1prim_sq / rx_sq) + (y1prim_sq / ry_sq)
        if radius_check > 1:
            rx *= sqrt(radius_check)
            ry *= sqrt(radius_check)
            rx_sq = rx * rx
            ry_sq = ry * ry

        t1 = rx_sq * y1prim_sq
        t2 = ry_sq * x1prim_sq
        c = sqrt(abs((rx_sq * ry_sq - t1 - t2) / (t1 + t2)))

        if self.arc == self.sweep:
            c = -c
        cxprim = c * rx * y1prim / ry
        cyprim = -c * ry * x1prim / rx

        self.center = complex((cosr * cxprim - sinr * cyprim) +
                              ((self.start.real + self.end.real) / 2),
                              (sinr * cxprim + cosr * cyprim) +
                              ((self.start.imag + self.end.imag) / 2))

        ux = (x1prim - cxprim) / rx
        uy = (y1prim - cyprim) / ry
        vx = (-x1prim - cxprim) / rx
        vy = (-y1prim - cyprim) / ry
        n = sqrt(ux * ux + uy * uy)
        p = ux
        theta = degrees(acos(p / n))
        if uy < 0:
            theta = -theta
        self.theta = theta % 360

        n = sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        p = ux * vx + uy * vy
        d = p/n
        # In certain cases the above calculation can through inaccuracies
        # become just slightly out of range, f ex -1.0000000000000002.
        if d > 1.0:
            d = 1.0
        elif d < -1.0:
            d = -1.0
        delta = degrees(acos(d))
        if (ux * vy - uy * vx) < 0:
            delta = -delta
        self.delta = delta % 360
        if not self.sweep:
            self.delta -= 360

    def point(self, pos):
        angle = radians(self.theta + (self.delta * pos))
        cosr = cos(radians(self.rotation))
        sinr = sin(radians(self.rotation))

        x = (cosr * cos(angle) * self.radius.real - sinr * sin(angle) *
             self.radius.imag + self.center.real)
        y = (sinr * cos(angle) * self.radius.real + cosr * sin(angle) *
             self.radius.imag + self.center.imag)
        return complex(x, y)

def _tokenize_path(pathdef):
    for x in COMMAND_RE.split(pathdef):
        if x in COMMANDS:
            yield x
        for token in FLOAT_RE.findall(x):
            yield token


def parse_path(pathdef, pen, current_pos=(0, 0)):
    """ Parse SVG path definition (i.e. "d" attribute of <path> elements)
    and call a 'pen' object's moveTo, lineTo, curveTo, qCurveTo and closePath
    methods.

    If 'current_pos' (2-float tuple) is provided, the initial moveTo will
    be relative to that instead being absolute.
    """
    # In the SVG specs, initial movetos are absolute, even if
    # specified as 'm'. This is the default behavior here as well.
    # But if you pass in a current_pos variable, the initial moveto
    # will be relative to that current_pos. This is useful.
    current_pos = complex(*current_pos)

    elements = list(_tokenize_path(pathdef))
    # Reverse for easy use of .pop()
    elements.reverse()

    start_pos = None
    command = None
    last_control = None

    while elements:

        if elements[-1] in COMMANDS:
            # New command.
            last_command = command  # Used by S and T
            command = elements.pop()
            absolute = command in UPPERCASE
            command = command.upper()
        else:
            # If this element starts with numbers, it is an implicit command
            # and we don't change the command. Check that it's allowed:
            if command is None:
                raise ValueError("Unallowed implicit command in %s, position %s" % (
                    pathdef, len(pathdef.split()) - len(elements)))
            last_command = command  # Used by S and T

        if command == 'M':
            # Moveto command.
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if absolute:
                current_pos = pos
            else:
                current_pos += pos

            # M is not preceded by Z; it's an open subpath
            if start_pos is not None:
                pen.endPath()

            pen.moveTo((current_pos.real, current_pos.imag))

            # when M is called, reset start_pos
            # This behavior of Z is defined in svg spec:
            # http://www.w3.org/TR/SVG/paths.html#PathDataClosePathCommand
            start_pos = current_pos

            # Implicit moveto commands are treated as lineto commands.
            # So we set command to lineto here, in case there are
            # further implicit commands after this moveto.
            command = 'L'

        elif command == 'Z':
            # Close path
            if current_pos != start_pos:
                pen.lineTo((start_pos.real, start_pos.imag))
            pen.closePath()
            current_pos = start_pos
            start_pos = None
            command = None  # You can't have implicit commands after closing.

        elif command == 'L':
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if not absolute:
                pos += current_pos
            pen.lineTo((pos.real, pos.imag))
            current_pos = pos

        elif command == 'H':
            x = elements.pop()
            pos = float(x) + current_pos.imag * 1j
            if not absolute:
                pos += current_pos.real
            pen.lineTo((pos.real, pos.imag))
            current_pos = pos

        elif command == 'V':
            y = elements.pop()
            pos = current_pos.real + float(y) * 1j
            if not absolute:
                pos += current_pos.imag * 1j
            pen.lineTo((pos.real, pos.imag))
            current_pos = pos

        elif command == 'C':
            control1 = float(elements.pop()) + float(elements.pop()) * 1j
            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control1 += current_pos
                control2 += current_pos
                end += current_pos

            pen.curveTo((control1.real, control1.imag),
                        (control2.real, control2.imag),
                        (end.real, end.imag))
            current_pos = end
            last_control = control2

        elif command == 'S':
            # Smooth curve. First control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'CS':
                # If there is no previous command or if the previous command
                # was not an C, c, S or s, assume the first control point is
                # coincident with the current point.
                control1 = current_pos
            else:
                # The first control point is assumed to be the reflection of
                # the second control point on the previous command relative
                # to the current point.
                control1 = current_pos + current_pos - last_control

            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control2 += current_pos
                end += current_pos

            pen.curveTo((control1.real, control1.imag),
                        (control2.real, control2.imag),
                        (end.real, end.imag))
            current_pos = end
            last_control = control2

        elif command == 'Q':
            control = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control += current_pos
                end += current_pos

            pen.qCurveTo((control.real, control.imag), (end.real, end.imag))
            current_pos = end
            last_control = control

        elif command == 'T':
            # Smooth curve. Control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'QT':
                # If there is no previous command or if the previous command
                # was not an Q, q, T or t, assume the first control point is
                # coincident with the current point.
                control = current_pos
            else:
                # The control point is assumed to be the reflection of
                # the control point on the previous command relative
                # to the current point.
                control = current_pos + current_pos - last_control

            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            pen.qCurveTo((control.real, control.imag), (end.real, end.imag))
            current_pos = end
            last_control = control

        elif command == 'A':
            # Arc
            radius = float(elements.pop()) + float(elements.pop()) * 1j
            rotation = float(elements.pop())
            arc = float(elements.pop())
            sweep = float(elements.pop())
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            if end == current_pos:
                # Guard against a situation where arc start and end being same.
                # That results division by zero issues in Arc parameterization.
                end += 0.00009
            svg_arc = Arc(current_pos, radius, rotation, arc, sweep, end)
            arc_points = []
            for point in [0.2, 0.4, 0.6, 0.8, 1]:
                # There are infinite points in an arc, but for our context,
                # define the arc using 5 points.
                arc_point = svg_arc.point(point)
                arc_points.append((arc_point.real, arc_point.imag))
            pen.qCurveTo(*arc_points)
            current_pos = end

    # no final Z command, it's an open path
    if start_pos is not None:
        pen.endPath()
