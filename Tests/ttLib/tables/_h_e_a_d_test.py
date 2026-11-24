from fontTools.misc import sstruct
from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.misc.timeTools import epoch_diff, timestampToString
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._h_e_a_d import headFormat, log
import calendar
import pytest


def make_head_data(created, modified):
    head = newTable("head")
    head.tableVersion = 1.0
    head.fontRevision = 1.0
    head.checkSumAdjustment = 0
    head.magicNumber = 0x5F0F3CF5
    head.flags = 0
    head.unitsPerEm = 1000
    head.created = created
    head.modified = modified
    head.xMin = head.yMin = head.xMax = head.yMax = 0
    head.macStyle = 0
    head.lowestRecPPEM = 8
    head.fontDirectionHint = 2
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0
    return sstruct.pack(headFormat, head)


def decompile(created, modified):
    head = newTable("head")
    head.decompile(make_head_data(created, modified), TTFont())
    return head


def test_decompile_unix_timestamps_converted_to_mac_epoch():
    unix = calendar.timegm((2015, 1, 3, 22, 4, 10, 0, 0, 0))
    with CapturingLogHandler(log, "WARNING") as captor:
        head = decompile(unix, unix)
    assert timestampToString(head.created) == "Sat Jan  3 22:04:10 2015"
    assert timestampToString(head.modified) == "Sat Jan  3 22:04:10 2015"
    captor.assertRegex("seems very low")


def test_decompile_unix_epoch_zero():
    # a unix timestamp of 0 is 1970-01-01 00:00:00 UTC exactly. Check the raw value:
    # timestampToString clamps anything before 1970 to zero, which would hide an offset
    # that is too small.
    head = decompile(0, 0)
    assert head.created == -epoch_diff
    assert head.modified == -epoch_diff


def test_decompile_mac_timestamps_unchanged():
    # 1970-01-01 00:00:00 UTC, the boundary between the two interpretations
    boundary = -epoch_diff
    with CapturingLogHandler(log, "WARNING") as captor:
        head = decompile(boundary, boundary + 1)
    assert head.created == boundary
    assert head.modified == boundary + 1
    assert not captor.records


def test_decompile_just_below_boundary_is_unix_timestamp():
    # one second below the boundary is still read as a unix timestamp
    below = -epoch_diff - 1
    with CapturingLogHandler(log, "WARNING") as captor:
        head = decompile(below, below)
    assert head.created == below - epoch_diff
    assert head.modified == below - epoch_diff
    captor.assertRegex("seems very low")
