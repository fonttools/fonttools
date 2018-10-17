# coding: utf-8
from __future__ import absolute_import, unicode_literals
from fontTools.misc import etree
from collections import OrderedDict
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
            "</axis>"
        ),
    ],
    ids=["simple_xml_no_indent", "simple_xml_indent", "xml_ns_attrib_utf_8"],
)
def test_roundtrip_string(xml):
    root = etree.fromstring(xml.encode("utf-8"))
    result = etree.tostring(root, encoding="utf-8").decode("utf-8")
    assert result == xml


def test_pretty_print():
    root = etree.Element("root")
    attrs = OrderedDict([("c", "2"), ("b", "1"), ("a", "0")])
    etree.SubElement(root, "element", attrs).text = "text"
    etree.SubElement(root, "element").text = "text"
    root.append(etree.Element("empty-element"))

    result = etree.tostring(root, encoding="unicode", pretty_print=True)

    assert result == (
        "<root>\n"
        '  <element c="2" b="1" a="0">text</element>\n'
        "  <element>text</element>\n"
        "  <empty-element/>\n"
        "</root>\n"
    )
