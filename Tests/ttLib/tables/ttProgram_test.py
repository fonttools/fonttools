from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.misc.textTools import deHexStr
import array
from io import StringIO
import os
import unittest

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, "data")

TTPROGRAM_TTX = os.path.join(DATA_DIR, "ttProgram.ttx")
# TTPROGRAM_BIN = os.path.join(DATA_DIR, "ttProgram.bin")

ASSEMBLY = [
    "PUSH[ ]",
    "0 4 3",
    "INSTCTRL[ ]",
    "POP[ ]",
]

BYTECODE = deHexStr(
    "403b3a393837363534333231302f2e2d2c2b2a292827262524232221201f1e1d1c1b1a"
    "191817161514131211100f0e0d0c0b0a090807060504030201002c01b0184358456ab0"
    "194360b0462344231020b0464ef04d2fb000121b21231133592d2c01b0184358b0052b"
    "b000134bb0145058b100403859b0062b1b21231133592d2c01b01843584eb0032510f2"
    "21b000124d1b2045b00425b00425234a6164b0285258212310d61bb0032510f221b000"
    "1259592d2cb01a435821211bb00225b0022549b00325b003254a612064b01050582121"
    "211bb00325b0032549b0005058b0005058b8ffe238211bb0103821591bb0005258b01e"
    "38211bb8fff03821595959592d2c01b0184358b0052bb000134bb0145058b90000ffc0"
    "3859b0062b1b21231133592d2c4e018a10b146194344b00014b10046e2b00015b90000"
    "fff03800b0003cb0282bb0022510b0003c2d2c0118b0002fb00114f2b00113b001154d"
    "b000122d2c01b0184358b0052bb00013b90000ffe038b0062b1b21231133592d2c01b0"
    "18435845646a23456469b01943646060b0462344231020b046f02fb000121b2121208a"
    "208a525811331b212159592d2c01b10b0a432343650a2d2c00b10a0b4323430b2d2c00"
    "b0462370b101463e01b0462370b10246453ab10200080d2d2cb0122bb0022545b00225"
    "456ab0408b60b0022523442121212d2cb0132bb0022545b00225456ab8ffc08c60b002"
    "2523442121212d2cb000b0122b2121212d2cb000b0132b2121212d2c01b00643b00743"
    "650a2d2c2069b04061b0008b20b12cc08a8cb8100062602b0c642364615c58b0036159"
    "2d2cb1000325456854b01c4b505a58b0032545b0032545606820b004252344b0042523"
    "441bb00325204568208a2344b00325456860b003252344592d2cb00325204568208a23"
    "44b003254564686560b00425b0016023442d2cb00943588721c01bb01243588745b011"
    "2bb0472344b0477ae41b038a45186920b04723448a8a8720b0a05158b0112bb0472344"
    "b0477ae41b21b0477ae4595959182d2c208a4523456860442d2c456a422d2c01182f2d"
    "2c01b0184358b00425b00425496423456469b0408b6120b080626ab00225b00225618c"
    "b0194360b0462344218a10b046f6211b21212121592d2c01b0184358b0022545b00225"
    "4564606ab00325456a6120b00425456a208a8b65b0042523448cb00325234421211b20"
    "456a4420456a44592d2c012045b00055b018435a584568234569b0408b6120b080626a"
    "208a236120b003258b65b0042523448cb00325234421211b2121b0192b592d2c018a8a"
    "45642345646164422d2cb00425b00425b0192bb0184358b00425b00425b00325b01b2b"
    "01b0022543b04054b0022543b000545a58b003252045b040614459b0022543b00054b0"
    "022543b040545a58b004252045b04060445959212121212d2c014b525843b002254523"
    "61441b2121592d2c014b525843b00225452360441b2121592d2c4b525845441b212159"
    "2d2c0120b003252349b04060b0206320b000525823b002253823b002256538008a6338"
    "1b212121212159012d2c4b505845441b2121592d2c01b005251023208af500b0016023"
    "edec2d2c01b005251023208af500b0016123edec2d2c01b0062510f500edec2d2c4623"
    "46608a8a462320468a608a61b8ff8062232010238ab14b4b8a70456020b0005058b001"
    "61b8ffba8b1bb0468c59b0106068013a2d2c2045b00325465258b0022546206861b003"
    "25b003253f2321381b2111592d2c2045b00325465058b0022546206861b00325b00325"
    "3f2321381b2111592d2c00b00743b006430b2d2c8a10ec2d2cb00c4358211b2046b000"
    "5258b8fff0381bb0103859592d2c20b0005558b8100063b003254564b00325456461b0"
    "005358b0021bb04061b00359254569535845441b2121591b21b0022545b00225456164"
    "b028515845441b212159592d2c21210c6423648bb84000622d2c21b08051580c642364"
    "8bb82000621bb200402f2b59b002602d2c21b0c051580c6423648bb81555621bb20080"
    "2f2b59b002602d2c0c6423648bb84000626023212d2c4b5358b00425b0042549642345"
    "6469b0408b6120b080626ab00225b00225618cb0462344218a10b046f6211b218a1123"
    "1220392f592d2cb00225b002254964b0c05458b8fff838b008381b2121592d2cb01343"
    "58031b02592d2cb0134358021b03592d2cb00a2b2310203cb0172b2d2cb00225b8fff0"
    "38b0282b8a102320d023b0102bb0054358c01b3c59201011b00012012d2c4b53234b51"
    "5a58381b2121592d2c01b0022510d023c901b00113b0001410b0013cb001162d2c01b0"
    "0013b001b0032549b0031738b001132d2c4b53234b515a5820458a60441b2121592d2c"
    "20392f2d"
)


class TestFont(object):
    disassembleInstructions = True


class ProgramTest(unittest.TestCase):
    def test__bool__(self):
        p = Program()
        assert not bool(p)

        bc = array.array("B", [0])
        p.fromBytecode(bc)
        assert bool(p)

        assert p.bytecode.pop() == 0
        assert not bool(p)

        p = Program()
        asm = ["SVTCA[0]"]
        p.fromAssembly(asm)
        assert bool(p)

        assert p.assembly.pop() == "SVTCA[0]"
        assert not bool(p)

    def test_from_assembly_list(self):
        p = Program()
        p.fromAssembly(ASSEMBLY)
        asm = p.getAssembly(preserve=True)
        assert ASSEMBLY == asm

    def test_from_assembly_str(self):
        p = Program()
        p.fromAssembly("\n".join(ASSEMBLY))
        asm = p.getAssembly(preserve=True)
        assert ASSEMBLY == asm

    def test_roundtrip(self):
        p = Program()
        p.fromBytecode(BYTECODE)
        asm = p.getAssembly(preserve=True)
        p.fromAssembly(asm)
        assert BYTECODE == p.getBytecode()

    def test_xml_indentation(self):
        with open(TTPROGRAM_TTX, "r", encoding="utf-8") as f:
            ttProgramXML = f.read()
        p = Program()
        p.fromBytecode(BYTECODE)
        ttfont = TestFont()
        buf = StringIO()
        writer = XMLWriter(buf)
        try:
            p.toXML(writer, ttfont)
        finally:
            output_string = buf.getvalue()
        assert output_string == ttProgramXML


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
