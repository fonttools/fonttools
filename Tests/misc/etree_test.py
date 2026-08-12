# coding: utf-8
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


def test_no_external_entity_expansion(tmp_path):
    # NOTE: only lxml < 5.0 ever resolved these, so on a newer lxml (and on the
    # ElementTree backend) this passes either way; it guards the old versions
    # that setup.py still allows.
    secret = tmp_path / "secret.txt"
    secret.write_text("s3cr3t")
    xml = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "%s">]>'
        "<root>&xxe;</root>" % secret.as_uri()
    ).encode("utf-8")

    try:
        root = etree.fromstring(xml, parser=etree.XMLParser())
    except etree.ParseError:
        # the undefined entity is rejected outright
        return

    assert "s3cr3t" not in etree.tostring(root, encoding="unicode")
