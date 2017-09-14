from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from .otBase import BaseTTXConverter
from . import DefaultTable
from . import grUtils
import struct

Feat_hdr_format='''
    >
    version:    16.16F
'''

class table_F__e_a_t(DefaultTable.DefaultTable):

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.features = {}

    def decompile(self, data, ttFont):
        (_, data) = sstruct.unpack2(Feat_hdr_format, data, self)
        numFeats, = struct.unpack('>H', data[:2])
        data = data[8:]
        allfeats = []
        maxsetting = 0
        for i in range(numFeats):
            if self.version >= 2.0:
                (fid, nums, _, offset, flags, lid) = struct.unpack(">LHHLHH",
                                                            data[16*i:16*(i+1)])
                offset = int((offset - 12 - 16 * numFeats) / 4)
            else:
                (fid, nums, offset, flags, lid) = struct.unpack(">HHLHH",
                                                            data[12*i:12*(i+1)])
                offset = int((offset - 12 - 12 * numFeats) / 4)
            allfeats.append((fid, nums, offset, flags, lid))
            maxsetting = max(maxsetting, offset + nums)
        data = data[16*numFeats:]
        allsettings = []
        for i in range(maxsetting):
            if len(data) >= 4 * (i + 1):
                (val, lid) = struct.unpack(">HH", data[4*i:4*(i+1)])
                allsettings.append((val, lid))
        for f in allfeats:
            (fid, nums, offset, flags, lid) = f
            fobj = Feature()
            fobj.flags = flags
            fobj.label = lid
            self.features[grUtils.num2tag(fid)] = fobj
            fobj.settings = {}
            for i in range(offset, offset + nums):
                if i >= len(allsettings): continue
                (vid, vlid) = allsettings[i]
                fobj.settings[vid] = vlid

    def compile(self, ttFont):
        fdat = ""
        vdat = ""
        offset = 0
        for f, v in sorted(self.features.items()):
            if self.version >= 2.0:
                fdat += struct.pack(">LHHLHH", grUtils.tag2num(f), len(v.settings),
                    0, offset * 4 + 12 + 16 * len(self.features), v.flags, v.label)
            else:
                fdat += struct.pack(">HHLHH", grUtils.tag2num(f), len(v.settings),
                    offset * 4 + 12 + 12 * len(self.features), v.flags, v.label)
            for s, l in sorted(v.settings.items()):
                vdat += struct.pack(">HH", s, l)
            offset += len(v.settings)
        hdr = sstruct.pack(Feat_hdr_format, self)
        return hdr + struct.pack('>HHL', len(self.features), 0, 0) + fdat + vdat

    def toXML(self, writer, ttFont):
        writer.simpletag('version', version=self.version)
        writer.newline()
        for f, v in sorted(self.features.items()):
            writer.begintag('feature', fid=f, label=v.label, flags=v.flags)
            writer.newline()
            for s, l in sorted(v.settings.items()):
                writer.simpletag('setting', value=s, label=l)
                writer.newline()
            writer.endtag('feature')
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == 'version':
            self.version = float(safeEval(attrs['version']))
        elif name == 'feature':
            fid = attrs['fid']
            fobj = Feature()
            fobj.flags = int(safeEval(attrs['flags']))
            fobj.label = int(safeEval(attrs['label']))
            self.features[fid] = fobj
            fobj.settings = {}
            for element in content:
                if not isinstance(element, tuple): continue
                tag, a, c = element
                if tag == 'setting':
                    fobj.settings[int(safeEval(a['value']))] = int(safeEval(a['label']))

class Feature(object):
    pass

