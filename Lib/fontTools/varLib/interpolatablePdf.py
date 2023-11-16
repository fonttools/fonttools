from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.cairoPen import CairoPen
from fontTools.varLib.interpolatable import PerContourOrComponentPen
from itertools import cycle
import cairo
import math


class InterpolatablePdf:
    width = 640
    height = 480
    pad = 16
    line_height = 36
    head_color = (0.3, 0.3, 0.3)
    label_color = (0.2, 0.2, 0.2)
    border_color = (0.9, 0.9, 0.9)
    border_width = 1
    fill_color = (0.8, 0.8, 0.8)
    stroke_color = (0.1, 0.1, 0.1)
    stroke_width = 2
    oncurve_node_color = (0, 0.8, 0)
    oncurve_node_diameter = 10
    offcurve_node_color = (0, 0.5, 0)
    offcurve_node_diameter = 8
    handle_color = (0.2, 1, 0.2)
    handle_width = 1
    start_point_color = (1, 0, 0)
    start_point_width = 15
    start_handle_color = (0.8, 0, 0)
    start_handle_width = 5
    start_handle_length = 100
    start_handle_arrow_length = 5
    contour_colors = ((1, 0, 0), (0, 0, 1), (0, 1, 0), (1, 1, 0), (1, 0, 1), (0, 1, 1))
    contour_alpha = 0.5
    cupcake_color = (0.3, 0, 0.3)
    cupcake = r"""
                          ,@.
                        ,@.@@,.
                  ,@@,.@@@.  @.@@@,.
                ,@@. @@@.     @@. @@,.
        ,@@@.@,.@.              @.  @@@@,.@.@@,.
   ,@@.@.     @@.@@.            @,.    .@’ @’  @@,
 ,@@. @.          .@@.@@@.  @@’                  @,
,@.  @@.                                          @,
@.     @,@@,.     ,                             .@@,
@,.       .@,@@,.         .@@,.  ,       .@@,  @, @,
@.                             .@. @ @@,.    ,      @
 @,.@@.     @,.      @@,.      @.           @,.    @’
  @@||@,.  @’@,.       @@,.  @@ @,.        @’@@,  @’
     \\@@@@’  @,.      @’@@@@’   @@,.   @@@’ //@@@’
      |||||||| @@,.  @@’ |||||||  |@@@|@||  ||
       \\\\\\\  ||@@@||  |||||||  |||||||  //
        |||||||  ||||||  ||||||   ||||||  ||
         \\\\\\  ||||||  ||||||  ||||||  //
          ||||||  |||||  |||||   |||||  ||
           \\\\\  |||||  |||||  |||||  //
            |||||  ||||  |||||  ||||  ||
             \\\\  ||||  ||||  ||||  //
              ||||||||||||||||||||||||
"""
    shrug_color = (0, 0.3, 0.3)
    shrug = r"""¯\_(")_/¯"""

    def __init__(self, outfile, glyphsets, names=None, **kwargs):
        self.outfile = outfile
        self.glyphsets = glyphsets
        self.names = names or [repr(g) for g in glyphsets]

        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise TypeError("Unknown keyword argument: %s" % k)
            setattr(self, k, v)

    def __enter__(self):
        self.surface = cairo.PDFSurface(self.outfile, self.width, self.height)
        return self

    def __exit__(self, type, value, traceback):
        self.surface.finish()

    def add_problems(self, problems):
        for glyph, glyph_problems in problems.items():
            for p in glyph_problems:
                self.add_problem(glyph, p)

    def add_problem(self, glyphname, p):
        master_keys = ("master",) if "master" in p else ("master_1", "master_2")
        master_indices = [self.names.index(p[k]) for k in master_keys]

        total_width = self.width + 2 * self.pad
        total_height = (
            self.pad
            + self.line_height
            + self.pad
            + len(master_indices) * (self.height + self.pad * 2 + self.line_height)
            + self.pad
        )

        self.surface.set_size(total_width, total_height)

        x = self.pad
        y = self.pad

        self.draw_label(glyphname, y=y, color=self.head_color, align=0)
        self.draw_label(p["type"], y=y, color=self.head_color, align=1)
        y += self.line_height + self.pad

        for master_idx in master_indices:
            glyphset = self.glyphsets[master_idx]
            name = self.names[master_idx]

            self.draw_label(name, y=y, color=self.label_color, align=0.5)
            y += self.line_height + self.pad

            if glyphset[glyphname] is not None:
                self.draw_glyph(glyphset, glyphname, p, x=x, y=y)
            else:
                self.draw_shrug()

            y += self.height + self.pad

        self.surface.show_page()

    def draw_label(self, label, *, y=0, color=(0, 0, 0), align=0):
        cr = cairo.Context(self.surface)
        cr.select_font_face("@cairo", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(self.line_height)
        font_extents = cr.font_extents()
        font_size = self.line_height * self.line_height / font_extents[2]
        cr.set_font_size(font_size)
        font_extents = cr.font_extents()

        cr.set_source_rgb(*color)

        extents = cr.text_extents(label)
        if extents.width > self.width:
            # Shrink
            font_size *= self.width / extents.width
            cr.set_font_size(font_size)
            font_extents = cr.font_extents()
            extents = cr.text_extents(label)

        # Center
        label_x = (self.width - extents.width) * align + self.pad
        label_y = y + font_extents[0]
        cr.move_to(label_x, label_y)
        cr.show_text(label)

    def draw_glyph(self, glyphset, glyphname, problem, *, x=0, y=0):
        problem_type = problem["type"]
        glyph = glyphset[glyphname]

        recording = RecordingPen()
        glyph.draw(recording)

        boundsPen = ControlBoundsPen(glyphset)
        recording.replay(boundsPen)

        glyph_width = boundsPen.bounds[2] - boundsPen.bounds[0]
        glyph_height = boundsPen.bounds[3] - boundsPen.bounds[1]

        scale = min(self.width / glyph_width, self.height / glyph_height)

        cr = cairo.Context(self.surface)
        cr.translate(x, y)
        # Center
        cr.translate(
            (self.width - glyph_width * scale) / 2,
            (self.height - glyph_height * scale) / 2,
        )
        cr.scale(scale, -scale)
        cr.translate(-boundsPen.bounds[0], -boundsPen.bounds[3])

        if self.border_color:
            cr.set_source_rgb(*self.border_color)
            cr.rectangle(
                boundsPen.bounds[0], boundsPen.bounds[1], glyph_width, glyph_height
            )
            cr.set_line_width(self.border_width / scale)
            cr.stroke()

        if self.fill_color and problem_type != "open_path":
            pen = CairoPen(glyphset, cr)
            recording.replay(pen)
            cr.set_source_rgb(*self.fill_color)
            cr.fill()

        if self.stroke_color:
            pen = CairoPen(glyphset, cr)
            recording.replay(pen)
            cr.set_source_rgb(*self.stroke_color)
            cr.set_line_width(self.stroke_width / scale)
            cr.stroke()

        if problem_type in ("node_count", "node_incompatibility"):
            cr.set_line_cap(cairo.LINE_CAP_ROUND)

            # Oncurve nodes
            for segment, args in recording.value:
                if not args:
                    continue
                x, y = args[-1]
                cr.move_to(x, y)
                cr.line_to(x, y)
            cr.set_source_rgb(*self.oncurve_node_color)
            cr.set_line_width(self.oncurve_node_diameter / scale)
            cr.stroke()

            # Offcurve nodes
            for segment, args in recording.value:
                for x, y in args[:-1]:
                    cr.move_to(x, y)
                    cr.line_to(x, y)
            cr.set_source_rgb(*self.offcurve_node_color)
            cr.set_line_width(self.offcurve_node_diameter / scale)
            cr.stroke()

            # Handles
            for segment, args in recording.value:
                if not args:
                    pass
                elif segment in ("moveTo", "lineTo"):
                    cr.move_to(*args[0])
                elif segment == "qCurveTo":
                    for x, y in args:
                        cr.line_to(x, y)
                    cr.new_sub_path()
                    cr.move_to(*args[-1])
                elif segment == "curveTo":
                    cr.line_to(*args[0])
                    cr.new_sub_path()
                    cr.move_to(*args[1])
                    cr.line_to(*args[2])
                    cr.new_sub_path()
                    cr.move_to(*args[-1])
                else:
                    assert False

            cr.set_source_rgb(*self.handle_color)
            cr.set_line_width(self.handle_width / scale)
            cr.stroke()

        if problem_type == "wrong_start_point":
            idx = problem["contour"]

            # Draw start point
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            i = 0
            for segment, args in recording.value:
                if segment == "moveTo":
                    if i == idx:
                        cr.move_to(*args[0])
                        cr.line_to(*args[0])
                    i += 1

            cr.set_source_rgb(*self.start_point_color)
            cr.set_line_width(self.start_point_width / scale)
            cr.stroke()

            # Draw arrow
            cr.set_line_cap(cairo.LINE_CAP_SQUARE)
            first_pt = None
            i = 0
            for segment, args in recording.value:
                if segment == "moveTo":
                    first_pt = args[0]
                    continue
                if first_pt is None:
                    continue
                second_pt = args[0]

                if i == idx:
                    first_pt = complex(*first_pt)
                    second_pt = complex(*second_pt)
                    length = abs(second_pt - first_pt)
                    if length:
                        # Draw handle
                        length *= scale
                        second_pt = (
                            first_pt
                            + (second_pt - first_pt) / length * self.start_handle_length
                        )
                        cr.move_to(first_pt.real, first_pt.imag)
                        cr.line_to(second_pt.real, second_pt.imag)
                        # Draw arrowhead
                        cr.save()
                        cr.translate(second_pt.real, second_pt.imag)
                        cr.rotate(
                            math.atan2(
                                second_pt.imag - first_pt.imag,
                                second_pt.real - first_pt.real,
                            )
                        )
                        cr.translate(self.start_handle_width, 0)
                        cr.move_to(0, 0)
                        cr.scale(1 / scale, 1 / scale)
                        cr.line_to(
                            -self.start_handle_arrow_length,
                            -self.start_handle_arrow_length,
                        )
                        cr.line_to(
                            -self.start_handle_arrow_length,
                            self.start_handle_arrow_length,
                        )
                        cr.close_path()
                        cr.restore()

                first_pt = None
                i += 1

            cr.set_source_rgb(*self.start_handle_color)
            cr.set_line_width(self.start_handle_width / scale)
            cr.stroke()

        if problem_type == "contour_order":
            matching = problem["value_2"]
            colors = cycle(self.contour_colors)
            perContourPen = PerContourOrComponentPen(RecordingPen, glyphset=glyphset)
            recording.replay(perContourPen)
            for i, contour in enumerate(perContourPen.value):
                if matching[i] == i:
                    continue
                color = next(colors)
                contour.replay(CairoPen(glyphset, cr))
                cr.set_source_rgba(*color, self.contour_alpha)
                cr.fill()

    def draw_cupcake(self):
        cupcake = self.cupcake.splitlines()
        cr = cairo.Context(self.surface)
        cr.set_source_rgb(*self.cupcake_color)
        cr.set_font_size(self.line_height)
        cr.select_font_face(
            "monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL
        )
        width = 0
        height = 0
        for line in cupcake:
            extents = cr.text_extents(line)
            width = max(width, extents.width)
            height += extents.height
        cr.scale(self.width / width, self.height / height)
        for line in cupcake:
            cr.translate(0, cr.text_extents(line).height)
            cr.move_to(0, 0)
            cr.show_text(line)

    def draw_shrug(self):
        cr = cairo.Context(self.surface)
        cr.set_source_rgb(*self.shrug_color)
        cr.set_font_size(self.line_height)
        cr.select_font_face(
            "monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL
        )
        extents = cr.text_extents(self.shrug)
        cr.translate(0, self.height * 0.8)
        scale = min(self.width / extents.width, self.height / extents.height)
        cr.scale(scale, scale)
        cr.move_to(0, 0)
        cr.show_text(self.shrug)
