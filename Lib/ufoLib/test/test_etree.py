# coding: utf-8
from __future__ import absolute_import, unicode_literals
from ufoLib import etree
import io
import pytest


@pytest.mark.parametrize(
    "xml",
    [
        (
            "<root>"
            '<element key="value">text</element>'
            "<element>text</element>tail"
            "<empty-element/>"
            "</root>"
        ),
        (
            "<root>\n"
            '  <element key="value">text</element>\n'
            "  <element>text</element>tail\n"
            "  <empty-element/>\n"
            "</root>"
        ),
        (
            '<axis default="400" maximum="1000" minimum="1" name="weight" tag="wght">'
            '<labelname xml:lang="fa-IR">قطر</labelname>'
            '</axis>'
        )
    ],
    ids=[
        "simple_xml_no_indent",
        "simple_xml_indent",
        "xml_ns_attrib_utf_8",
    ]
)
def test_roundtrip_string(xml):
    root = etree.fromstring(xml.encode("utf-8"))
    result = etree.tostring(root, encoding="utf-8").decode("utf-8")
    assert result == xml
