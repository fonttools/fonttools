from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from itertools import *
from functools import partial
from . import DefaultTable
import struct, operator, warnings
try:
    import lz4
except: 
    lz4 = None


Glat_format_0 = """
    >        # big endian
    version: 16.16F
"""

Glat_format_3_addition = """
    >
    compression:L    # compression scheme or reserved 
"""

Glat_format_1_entry = """
    >
    attNum:     B    # Attribute number of first attribute
    num:        B    # Number of attributes in this run
"""
Glat_format_23_entry = """
    >
    attNum:     H    # Attribute number of first attribute
    num:        H    # Number of attributes in this run
"""

Glat_format_3_octabox_metrics = """
    >
    subboxBitmap:   H    # Which subboxes exist on 4x4 grid
    diagNegMin:     B    # Defines minimum negatively-sloped diagonal (si)
    diagNegMax:     B    # Defines maximum negatively-sloped diagonal (sa)
    diagPosMin:     B    # Defines minimum positively-sloped diagonal (di)
    diagPosMax:     B    # Defines maximum positively-sloped diagonal (da)
"""

Glat_format_3_subbox_entry = """
    >
    left:           B    # xi
    right:          B    # xa
    bottom:         B    # yi
    top:            B    # ya
    diagNegMin:     B    # Defines minimum negatively-sloped diagonal (si)
    diagNegMax:     B    # Defines maximum negatively-sloped diagonal (sa)
    diagPosMin:     B    # Defines minimum positively-sloped diagonal (di)
    diagPosMax:     B    # Defines maximum positively-sloped diagonal (da)
"""

class _Object() :
    pass

class _Dict(dict) :
    pass

class table_G__l_a_t(DefaultTable.DefaultTable):
    '''
    Support Graphite Glat tables
    '''

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.scheme = 0

    def decompress(self, size, data):
        if self.scheme == 0:
            pass
        elif self.scheme == 1 and lz4:
            res = lz4.decompress(struct.pack("<L", size) + data)
            if (not res 
              or len(res) != size 
              or sstruct.unpack2(Glat_format_0, res)['version'] != self.version 
              or sstruct.unpack2(Glat_format_3_addition, res[4:]) >> 27 != 0):
                warnings.warn("Glat table decompression failed.")
            else:
                data = res
        else:
            warnings.warn("Glat table is compressed with an unsupported compression scheme.")
        return data
    
    def compress(self, data):
        hdr = {'compression' : (self.scheme << 27) + (len(data) & 0x07ffffff)}
        hdrdat = sstruct.pack(Glat_format_0, self) + sstruct.pack(Glat_format_3_addition, hdr)
        if self.scheme == 0 :
            res = data
        if self.scheme == 1 and lz4:
            res = lz4.compress(hdrdat + data, 16, content_size_header=False)
        return hdrdat + res

    def decompile(self, data, ttFont):
        sstruct.unpack2(Glat_format_0, data, self)
        if self.version == 1.0:
            decoder = partial(self.decompileAttributes12,fmt=Glat_format_1_entry)
        elif self.version == 2.0:   
            decoder = partial(self.decompileAttributes12,fmt=Glat_format_23_entry)
        elif self.version == 3.0:
            hdr, _ = sstruct.unpack2(Glat_format_3_addition, data[4:])
            self.scheme = hdr['compression'] >> 27
            if self.scheme :
                data = self.decompress(hdr['compression'] & 0x07ffffff, data[8:])
            decoder = self.decompileAttributes3
        
        gloc = ttFont['Gloc']
        self.attributes = {}
        glyphorder = ttFont.getGlyphOrder()
        count = 0
        numg = len(glyphorder)
        for s,e in zip(gloc,gloc[1:]):
            if count >= len(glyphorder):
                glyphorder.append('pseudo_{}'.format(count - numg + 1))
            self.attributes[glyphorder[count]] = decoder(data[s:e])
            count += 1
    
    def decompileAttributes12(self, data, fmt):
        attributes = _Dict()
        while len(data) > 3:
            e, data = sstruct.unpack2(fmt, data, _Object())
            keys = range(e.attNum, e.attNum+e.num)
            if len(data) >= 2 * e.num :
                vals = struct.unpack_from(('>%dh' % e.num), data)
                attributes.update(izip(keys,vals))
                data = data[2*e.num:]
        return attributes

    def decompileAttributes3(self, data):
        o, data = sstruct.unpack2(Glat_format_3_octabox_metrics, data, _Object())
        numsub = bin(o.subboxBitmap).count("1")
        o.subboxes = []
        for b in range(numsub):
            if len(data) >= 8 :
                subbox, data = sstruct.unpack2(Glat_format_3_subbox_entry, data, _Object())
                o.subboxes.append(subbox)
        attrs = self.decompileAttributes12(data, Glat_format_23_entry)
        attrs.octabox = o
        return attrs

    def compile(self, ttFont):
        data = sstruct.pack(Glat_format_0, self)
        if self.version == 1.0:
            encoder = partial(self.compileAttributes12, fmt=Glat_format_1_entry)
        elif self.version == 2.0:
            encoder = partial(self.compileAttributes12, fmt=Glat_format_1_entry)
        elif self.version == 3.0:
            compression = self.scheme << 27
            data += sstruct.pack(Glat_format_3_addition, {'compression': compression})
            encoder = self.compileAttributes3

        glocs = []
        glyphorder = ttFont.getGlyphOrder()
        count = 1
        gname = "pseudo_{}".format(count)
        while gname in self.attributes :
            glyphorder.append(gname)
            count += 1
            gname = "pseudo_{}".format(count)
        for n in glyphorder :
            glocs.append(len(data))
            data += encoder(self.attributes[n])
        glocs.append(len(data))
        ttFont['Gloc'].set(glocs)

        if self.version == 3.0:
            data = self.compress(data[8:])
        return data

    def compileAttributes12(self, attrs, fmt):
        data = []
        for e in entries(attrs):
            data.extend(sstruct.pack(fmt, e))
            data.extend(struct.pack(('>%dh' % len(e['values'])), *e['values']))
        return "".join(data)
    
    def compileAttributes3(self, attrs):
        o = attrs.octabox
        data = sstruct.pack(Glat_format_3_octabox_metrics, o)
        numsub = bin(o.subboxBitmap).count("1")
        for b in range(numsub) :
            data += sstruct.pack(Glat_format_3_subbox_entry, o.subboxes[b])
        return data + self.compileAttributes12(attrs, Glat_format_23_entry)

    def toXML(self, writer, ttFont):
        writer.simpletag('version', version=self.version)
        writer.newline()
        for n, a in sorted(self.attributes.items()):
            writer.begintag('glyph', name=n)
            writer.newline()
            if hasattr(a, 'octabox'):
                o = a.octabox
                formatstring, names, fixes = sstruct.getformat(Glat_format_3_octabox_metrics)
                vals = {}
                for k in names:
                    if k == 'subboxBitmap': continue
                    vals[k] = "{:.3f}%".format(getattr(o, k) * 100. / 256)
                vals['bitmap'] = "{:0X}".format(o.subboxBitmap)
                writer.begintag('octaboxes', **vals)
                writer.newline()
                formatstring, names, fixes = sstruct.getformat(Glat_format_3_subbox_entry)
                for s in o.subboxes:
                    vals = {}
                    for k in names:
                        vals[k] = "{:.3f}%".format(getattr(s, k) * 100. / 256)
                    writer.simpletag('octabox', **vals)
                    writer.newline()
                writer.endtag('octaboxes')
                writer.newline()
            for k, v in sorted(a.items()):
                writer.simpletag('attribute', index=k, value=v)
                writer.newline()
            writer.endtag('glyph')
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == 'version' :
            self.version = float(safeEval(attrs['version']))
        if name != 'glyph' : return
        if not hasattr(self, 'attributes'):
            self.attributes = {}
        gname = attrs['name']
        attributes = _Dict()
        for element in content:
            if not isinstance(element, tuple): continue
            tag, attrs, subcontent = element
            if tag == 'attribute' :
                k = int(safeEval(attrs['index']))
                v = int(safeEval(attrs['value']))
                attributes[k]=v
            elif tag == 'octaboxes':
                o = _Object()
                o.subboxBitmap = int(attrs['bitmap'], 16)
                o.subboxes = []
                del attrs['bitmap']
                for k, v in attrs.items():
                    setattr(o, k, int(float(v[:-1]) * 256. / 100. + 0.5))
                for element in subcontent:
                    if not isinstance(element, tuple): continue
                    (tag, attrs, subcontent) = element
                    so = _Object()
                    for k, v in attrs.items():
                        setattr(so, k, int(float(v[:-1]) * 256. / 100. + 0.5))
                    o.subboxes.append(so)
                attributes.octabox = o
        self.attributes[gname] = attributes
    
def _entries(attrs):
    ak = 0
    vals = []
    for k,v in attrs:
        if len(vals) and k != ak + 1 :
            yield {'attNum': ak - len(vals) + 1, 'num':len(vals), 'values':vals}
            vals = []
        ak = k
        vals.append(v)
    yield {'attNum': ak - len(vals) + 1, 'num':len(vals), 'values':vals}

def entries(attributes):
    g = _entries(sorted(attributes.iteritems(), key=lambda x:int(x[0])))
    return g
