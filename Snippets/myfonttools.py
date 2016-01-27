from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from codepoint_convert import convert_from_gbk

__author__ = 'bihicheng'

SUPPORT_CONVERT_FROM_ENCODE = ['gb2312', 'gbk']

class MyFontTools(object):
    def __init__(self, fontfile):
        self.font = TTFont(fontfile)

    def cmap_format_gbk2utf8(self):
        cmap = self.font['cmap']
        outtables = []
        for table in cmap.tables:
            if table.format in [4, 12, 13, 14]:
                outtables.append(table)
                
            # Convert ot format4
            if table.getEncoding() in SUPPORT_CONVERT_FROM_ENCODE:
                for gbk_code in table.cmap.keys():
                    uni_code= convert_from_gbk(gbk_code)
                    if gbk_code != uni_code:
                        table.cmap[uni_code] = table.cmap.pop(gbk_code)

                newtable = CmapSubtable.newSubtable(4)
                newtable.platformID = self.to_platformID
                newtable.platEncID = self.to_platEncID
                newtable.language = table.language
                newtable.cmap = table.cmap
                outtables.append(newtable)
        cmap.tables = outtables

    def vhea_fixed(self):
        self.font['vhea'].tableVersion=1.0


    def save(self, outfile):
        import pdb;pdb.set_trace()
        self.font.save(outfile)
