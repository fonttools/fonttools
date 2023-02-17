# Copyright 2016 Google Inc. All Rights Reserved.
# Copyright 2023 Behdad Esfahbod. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fontTools.qu2cu import quadratic_to_curve
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.reverseContourPen import ReverseContourPen


class Qu2CuPen(FilterPen):
    """A filter pen to convert quadratic bezier splines to cubic curves
    using the FontTools SegmentPen protocol.

    Args:

        other_pen: another SegmentPen used to draw the transformed outline.
        max_err: maximum approximation error in font units. For optimal results,
            if you know the UPEM of the font, we recommend setting this to a
            value equal, or close to UPEM / 1000.
        reverse_direction: flip the contours' direction but keep starting point.
        stats: a dictionary counting the point numbers of cubic segments.
    """

    def __init__(
        self,
        other_pen,
        max_err,
        reverse_direction=False,
        stats=None,
    ):
        if reverse_direction:
            other_pen = ReverseContourPen(other_pen)
        super().__init__(other_pen)
        self.max_err = max_err
        self.stats = stats

    def _quadratic_to_curve(self, points):
        quadratics = (self.current_pt,) + points
        curves = quadratic_to_curves(quadratics, self.max_err)
        if self.stats is not None:
            n = str(len(curves))
            self.stats[n] = self.stats.get(n, 0) + 1
        for curve in curves:
            self.curveTo(*curve[1:])

    def qCurveTo(self, *points):
        n = len(points)
        if n < 2:
            self.lineTo(*points)
        else:
            self._quadratic_to_curve(points)
