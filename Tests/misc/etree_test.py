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
    secret = tmp_path / "secret.txt"
    secret.write_text("s3cr3t")
    xml = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "%s">]>'
        "<root>&xxe;</root>" % secret.as_uri()
    ).encode("utf-8")

    try:
        root = etree.fromstring(xml, parser=etree.XMLParser())
    except etree.ParseError as e:
        # the undefined entity is rejected outright; the file must not have
        # been read into the error message either
        assert "s3cr3t" not in str(e)
    else:
        assert "s3cr3t" not in etree.tostring(root, encoding="unicode")


def test_no_external_parameter_entity_expansion(tmp_path):
    # lxml 5.0-6.1.2 still fetched external *parameter* entities with the
    # default resolve_entities="internal", which let an external DTD fragment
    # define a general entity holding the contents of a local file.
    secret = tmp_path / "secret.txt"
    secret.write_text("s3cr3t")
    dtd = tmp_path / "evil.dtd"
    dtd.write_text(
        '<!ENTITY %% sec SYSTEM "%s">\n<!ENTITY leak "%%sec;">\n' % secret.as_uri()
    )
    xml = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE root [<!ENTITY %% dtd SYSTEM "%s"> %%dtd;]>'
        "<root>&leak;</root>" % dtd.as_uri()
    ).encode("utf-8")

    try:
        root = etree.fromstring(xml, parser=etree.XMLParser())
    except etree.ParseError as e:
        # the undefined entity is rejected outright; the file must not have
        # been read into the error message either
        assert "s3cr3t" not in str(e)
    else:
        assert "s3cr3t" not in etree.tostring(root, encoding="unicode")
