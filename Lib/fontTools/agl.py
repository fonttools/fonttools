# The table below is taken from
# http://www.adobe.com/devnet/opentype/archives/aglfn.txt

_aglText = """\
# -----------------------------------------------------------
# Copyright 2003, 2005-2008, 2010 Adobe Systems Incorporated.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the
# following conditions are met:
#
# Redistributions of source code must retain the above
# copyright notice, this list of conditions and the following
# disclaimer.
#
# Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials
# provided with the distribution.
#
# Neither the name of Adobe Systems Incorporated nor the names
# of its contributors may be used to endorse or promote
# products derived from this software without specific prior
# written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------
# Name:          Adobe Glyph List For New Fonts
# Table version: 1.7
# Date:          November 6, 2008
# URL:           http://sourceforge.net/adobe/aglfn/
#
# Description:
#
# AGLFN (Adobe Glyph List For New Fonts) provides a list of base glyph
# names that are recommended for new fonts, which are compatible with
# the AGL (Adobe Glyph List) Specification, and which should be used
# as described in Section 6 of that document. AGLFN comprises the set
# of glyph names from AGL that map via the AGL Specification rules to
# the semantically correct UV (Unicode Value). For example, "Asmall"
# is omitted because AGL maps this glyph name to the PUA (Private Use
# Area) value U+F761, rather than to the UV that maps from the glyph
# name "A." Also omitted is "ffi," because AGL maps this to the
# Alphabetic Presentation Forms value U+FB03, rather than decomposing
# it into the following sequence of three UVs: U+0066, U+0066, and
# U+0069. The name "arrowvertex" has been omitted because this glyph
# now has a real UV, and AGL is now incorrect in mapping it to the PUA
# value U+F8E6. If you do not find an appropriate name for your glyph
# in this list, then please refer to Section 6 of the AGL
# Specification.
#
# Format: three semicolon-delimited fields:
#   (1) Standard UV or CUS UV--four uppercase hexadecimal digits
#   (2) Glyph name--upper/lowercase letters and digits
#   (3) Character names: Unicode character names for standard UVs, and
#       descriptive names for CUS UVs--uppercase letters, hyphen, and
#       space
#
# The records are sorted by glyph name in increasing ASCII order,
# entries with the same glyph name are sorted in decreasing priority
# order, the UVs and Unicode character names are provided for
# convenience, lines starting with "#" are comments, and blank lines
# should be ignored.
#
# Revision History:
#
# 1.7 [6 November 2008]
# - Reverted to the original 1.4 and earlier mappings for Delta,
#   Omega, and mu.
# - Removed mappings for "afii" names. These should now be assigned
#   "uni" names.
# - Removed mappings for "commaaccent" names. These should now be
#   assigned "uni" names.
#
# 1.6 [30 January 2006]
# - Completed work intended in 1.5.
#
# 1.5 [23 November 2005]
# - Removed duplicated block at end of file.
# - Changed mappings:
#   2206;Delta;INCREMENT changed to 0394;Delta;GREEK CAPITAL LETTER DELTA
#   2126;Omega;OHM SIGN changed to 03A9;Omega;GREEK CAPITAL LETTER OMEGA
#   03BC;mu;MICRO SIGN changed to 03BC;mu;GREEK SMALL LETTER MU
# - Corrected statement above about why "ffi" is omitted.
#
# 1.4 [24 September 2003]
# - Changed version to 1.4, to avoid confusion with the AGL 1.3.
# - Fixed spelling errors in the header.
# - Fully removed "arrowvertex," as it is mapped only to a PUA Unicode
#   value in some fonts.
#
# 1.1 [17 April 2003]
# - Renamed [Tt]cedilla back to [Tt]commaaccent.
#
# 1.0 [31 January 2003]
# - Original version.
# - Derived from the AGLv1.2 by:
#   removing the PUA area codes;
#   removing duplicate Unicode mappings; and
#   renaming "tcommaaccent" to "tcedilla" and "Tcommaaccent" to "Tcedilla"
#
0041;A;LATIN CAPITAL LETTER A
00C6;AE;LATIN CAPITAL LETTER AE
01FC;AEacute;LATIN CAPITAL LETTER AE WITH ACUTE
00C1;Aacute;LATIN CAPITAL LETTER A WITH ACUTE
0102;Abreve;LATIN CAPITAL LETTER A WITH BREVE
00C2;Acircumflex;LATIN CAPITAL LETTER A WITH CIRCUMFLEX
00C4;Adieresis;LATIN CAPITAL LETTER A WITH DIAERESIS
00C0;Agrave;LATIN CAPITAL LETTER A WITH GRAVE
0391;Alpha;GREEK CAPITAL LETTER ALPHA
0386;Alphatonos;GREEK CAPITAL LETTER ALPHA WITH TONOS
0100;Amacron;LATIN CAPITAL LETTER A WITH MACRON
0104;Aogonek;LATIN CAPITAL LETTER A WITH OGONEK
00C5;Aring;LATIN CAPITAL LETTER A WITH RING ABOVE
01FA;Aringacute;LATIN CAPITAL LETTER A WITH RING ABOVE AND ACUTE
00C3;Atilde;LATIN CAPITAL LETTER A WITH TILDE
0042;B;LATIN CAPITAL LETTER B
0392;Beta;GREEK CAPITAL LETTER BETA
0043;C;LATIN CAPITAL LETTER C
0106;Cacute;LATIN CAPITAL LETTER C WITH ACUTE
010C;Ccaron;LATIN CAPITAL LETTER C WITH CARON
00C7;Ccedilla;LATIN CAPITAL LETTER C WITH CEDILLA
0108;Ccircumflex;LATIN CAPITAL LETTER C WITH CIRCUMFLEX
010A;Cdotaccent;LATIN CAPITAL LETTER C WITH DOT ABOVE
03A7;Chi;GREEK CAPITAL LETTER CHI
0044;D;LATIN CAPITAL LETTER D
010E;Dcaron;LATIN CAPITAL LETTER D WITH CARON
0110;Dcroat;LATIN CAPITAL LETTER D WITH STROKE
2206;Delta;INCREMENT
0045;E;LATIN CAPITAL LETTER E
00C9;Eacute;LATIN CAPITAL LETTER E WITH ACUTE
0114;Ebreve;LATIN CAPITAL LETTER E WITH BREVE
011A;Ecaron;LATIN CAPITAL LETTER E WITH CARON
00CA;Ecircumflex;LATIN CAPITAL LETTER E WITH CIRCUMFLEX
00CB;Edieresis;LATIN CAPITAL LETTER E WITH DIAERESIS
0116;Edotaccent;LATIN CAPITAL LETTER E WITH DOT ABOVE
00C8;Egrave;LATIN CAPITAL LETTER E WITH GRAVE
0112;Emacron;LATIN CAPITAL LETTER E WITH MACRON
014A;Eng;LATIN CAPITAL LETTER ENG
0118;Eogonek;LATIN CAPITAL LETTER E WITH OGONEK
0395;Epsilon;GREEK CAPITAL LETTER EPSILON
0388;Epsilontonos;GREEK CAPITAL LETTER EPSILON WITH TONOS
0397;Eta;GREEK CAPITAL LETTER ETA
0389;Etatonos;GREEK CAPITAL LETTER ETA WITH TONOS
00D0;Eth;LATIN CAPITAL LETTER ETH
20AC;Euro;EURO SIGN
0046;F;LATIN CAPITAL LETTER F
0047;G;LATIN CAPITAL LETTER G
0393;Gamma;GREEK CAPITAL LETTER GAMMA
011E;Gbreve;LATIN CAPITAL LETTER G WITH BREVE
01E6;Gcaron;LATIN CAPITAL LETTER G WITH CARON
011C;Gcircumflex;LATIN CAPITAL LETTER G WITH CIRCUMFLEX
0120;Gdotaccent;LATIN CAPITAL LETTER G WITH DOT ABOVE
0048;H;LATIN CAPITAL LETTER H
25CF;H18533;BLACK CIRCLE
25AA;H18543;BLACK SMALL SQUARE
25AB;H18551;WHITE SMALL SQUARE
25A1;H22073;WHITE SQUARE
0126;Hbar;LATIN CAPITAL LETTER H WITH STROKE
0124;Hcircumflex;LATIN CAPITAL LETTER H WITH CIRCUMFLEX
0049;I;LATIN CAPITAL LETTER I
0132;IJ;LATIN CAPITAL LIGATURE IJ
00CD;Iacute;LATIN CAPITAL LETTER I WITH ACUTE
012C;Ibreve;LATIN CAPITAL LETTER I WITH BREVE
00CE;Icircumflex;LATIN CAPITAL LETTER I WITH CIRCUMFLEX
00CF;Idieresis;LATIN CAPITAL LETTER I WITH DIAERESIS
0130;Idotaccent;LATIN CAPITAL LETTER I WITH DOT ABOVE
2111;Ifraktur;BLACK-LETTER CAPITAL I
00CC;Igrave;LATIN CAPITAL LETTER I WITH GRAVE
012A;Imacron;LATIN CAPITAL LETTER I WITH MACRON
012E;Iogonek;LATIN CAPITAL LETTER I WITH OGONEK
0399;Iota;GREEK CAPITAL LETTER IOTA
03AA;Iotadieresis;GREEK CAPITAL LETTER IOTA WITH DIALYTIKA
038A;Iotatonos;GREEK CAPITAL LETTER IOTA WITH TONOS
0128;Itilde;LATIN CAPITAL LETTER I WITH TILDE
004A;J;LATIN CAPITAL LETTER J
0134;Jcircumflex;LATIN CAPITAL LETTER J WITH CIRCUMFLEX
004B;K;LATIN CAPITAL LETTER K
039A;Kappa;GREEK CAPITAL LETTER KAPPA
004C;L;LATIN CAPITAL LETTER L
0139;Lacute;LATIN CAPITAL LETTER L WITH ACUTE
039B;Lambda;GREEK CAPITAL LETTER LAMDA
013D;Lcaron;LATIN CAPITAL LETTER L WITH CARON
013F;Ldot;LATIN CAPITAL LETTER L WITH MIDDLE DOT
0141;Lslash;LATIN CAPITAL LETTER L WITH STROKE
004D;M;LATIN CAPITAL LETTER M
039C;Mu;GREEK CAPITAL LETTER MU
004E;N;LATIN CAPITAL LETTER N
0143;Nacute;LATIN CAPITAL LETTER N WITH ACUTE
0147;Ncaron;LATIN CAPITAL LETTER N WITH CARON
00D1;Ntilde;LATIN CAPITAL LETTER N WITH TILDE
039D;Nu;GREEK CAPITAL LETTER NU
004F;O;LATIN CAPITAL LETTER O
0152;OE;LATIN CAPITAL LIGATURE OE
00D3;Oacute;LATIN CAPITAL LETTER O WITH ACUTE
014E;Obreve;LATIN CAPITAL LETTER O WITH BREVE
00D4;Ocircumflex;LATIN CAPITAL LETTER O WITH CIRCUMFLEX
00D6;Odieresis;LATIN CAPITAL LETTER O WITH DIAERESIS
00D2;Ograve;LATIN CAPITAL LETTER O WITH GRAVE
01A0;Ohorn;LATIN CAPITAL LETTER O WITH HORN
0150;Ohungarumlaut;LATIN CAPITAL LETTER O WITH DOUBLE ACUTE
014C;Omacron;LATIN CAPITAL LETTER O WITH MACRON
2126;Omega;OHM SIGN
038F;Omegatonos;GREEK CAPITAL LETTER OMEGA WITH TONOS
039F;Omicron;GREEK CAPITAL LETTER OMICRON
038C;Omicrontonos;GREEK CAPITAL LETTER OMICRON WITH TONOS
00D8;Oslash;LATIN CAPITAL LETTER O WITH STROKE
01FE;Oslashacute;LATIN CAPITAL LETTER O WITH STROKE AND ACUTE
00D5;Otilde;LATIN CAPITAL LETTER O WITH TILDE
0050;P;LATIN CAPITAL LETTER P
03A6;Phi;GREEK CAPITAL LETTER PHI
03A0;Pi;GREEK CAPITAL LETTER PI
03A8;Psi;GREEK CAPITAL LETTER PSI
0051;Q;LATIN CAPITAL LETTER Q
0052;R;LATIN CAPITAL LETTER R
0154;Racute;LATIN CAPITAL LETTER R WITH ACUTE
0158;Rcaron;LATIN CAPITAL LETTER R WITH CARON
211C;Rfraktur;BLACK-LETTER CAPITAL R
03A1;Rho;GREEK CAPITAL LETTER RHO
0053;S;LATIN CAPITAL LETTER S
250C;SF010000;BOX DRAWINGS LIGHT DOWN AND RIGHT
2514;SF020000;BOX DRAWINGS LIGHT UP AND RIGHT
2510;SF030000;BOX DRAWINGS LIGHT DOWN AND LEFT
2518;SF040000;BOX DRAWINGS LIGHT UP AND LEFT
253C;SF050000;BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL
252C;SF060000;BOX DRAWINGS LIGHT DOWN AND HORIZONTAL
2534;SF070000;BOX DRAWINGS LIGHT UP AND HORIZONTAL
251C;SF080000;BOX DRAWINGS LIGHT VERTICAL AND RIGHT
2524;SF090000;BOX DRAWINGS LIGHT VERTICAL AND LEFT
2500;SF100000;BOX DRAWINGS LIGHT HORIZONTAL
2502;SF110000;BOX DRAWINGS LIGHT VERTICAL
2561;SF190000;BOX DRAWINGS VERTICAL SINGLE AND LEFT DOUBLE
2562;SF200000;BOX DRAWINGS VERTICAL DOUBLE AND LEFT SINGLE
2556;SF210000;BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE
2555;SF220000;BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE
2563;SF230000;BOX DRAWINGS DOUBLE VERTICAL AND LEFT
2551;SF240000;BOX DRAWINGS DOUBLE VERTICAL
2557;SF250000;BOX DRAWINGS DOUBLE DOWN AND LEFT
255D;SF260000;BOX DRAWINGS DOUBLE UP AND LEFT
255C;SF270000;BOX DRAWINGS UP DOUBLE AND LEFT SINGLE
255B;SF280000;BOX DRAWINGS UP SINGLE AND LEFT DOUBLE
255E;SF360000;BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE
255F;SF370000;BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE
255A;SF380000;BOX DRAWINGS DOUBLE UP AND RIGHT
2554;SF390000;BOX DRAWINGS DOUBLE DOWN AND RIGHT
2569;SF400000;BOX DRAWINGS DOUBLE UP AND HORIZONTAL
2566;SF410000;BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL
2560;SF420000;BOX DRAWINGS DOUBLE VERTICAL AND RIGHT
2550;SF430000;BOX DRAWINGS DOUBLE HORIZONTAL
256C;SF440000;BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL
2567;SF450000;BOX DRAWINGS UP SINGLE AND HORIZONTAL DOUBLE
2568;SF460000;BOX DRAWINGS UP DOUBLE AND HORIZONTAL SINGLE
2564;SF470000;BOX DRAWINGS DOWN SINGLE AND HORIZONTAL DOUBLE
2565;SF480000;BOX DRAWINGS DOWN DOUBLE AND HORIZONTAL SINGLE
2559;SF490000;BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE
2558;SF500000;BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE
2552;SF510000;BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE
2553;SF520000;BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE
256B;SF530000;BOX DRAWINGS VERTICAL DOUBLE AND HORIZONTAL SINGLE
256A;SF540000;BOX DRAWINGS VERTICAL SINGLE AND HORIZONTAL DOUBLE
015A;Sacute;LATIN CAPITAL LETTER S WITH ACUTE
0160;Scaron;LATIN CAPITAL LETTER S WITH CARON
015E;Scedilla;LATIN CAPITAL LETTER S WITH CEDILLA
015C;Scircumflex;LATIN CAPITAL LETTER S WITH CIRCUMFLEX
03A3;Sigma;GREEK CAPITAL LETTER SIGMA
0054;T;LATIN CAPITAL LETTER T
03A4;Tau;GREEK CAPITAL LETTER TAU
0166;Tbar;LATIN CAPITAL LETTER T WITH STROKE
0164;Tcaron;LATIN CAPITAL LETTER T WITH CARON
0398;Theta;GREEK CAPITAL LETTER THETA
00DE;Thorn;LATIN CAPITAL LETTER THORN
0055;U;LATIN CAPITAL LETTER U
00DA;Uacute;LATIN CAPITAL LETTER U WITH ACUTE
016C;Ubreve;LATIN CAPITAL LETTER U WITH BREVE
00DB;Ucircumflex;LATIN CAPITAL LETTER U WITH CIRCUMFLEX
00DC;Udieresis;LATIN CAPITAL LETTER U WITH DIAERESIS
00D9;Ugrave;LATIN CAPITAL LETTER U WITH GRAVE
01AF;Uhorn;LATIN CAPITAL LETTER U WITH HORN
0170;Uhungarumlaut;LATIN CAPITAL LETTER U WITH DOUBLE ACUTE
016A;Umacron;LATIN CAPITAL LETTER U WITH MACRON
0172;Uogonek;LATIN CAPITAL LETTER U WITH OGONEK
03A5;Upsilon;GREEK CAPITAL LETTER UPSILON
03D2;Upsilon1;GREEK UPSILON WITH HOOK SYMBOL
03AB;Upsilondieresis;GREEK CAPITAL LETTER UPSILON WITH DIALYTIKA
038E;Upsilontonos;GREEK CAPITAL LETTER UPSILON WITH TONOS
016E;Uring;LATIN CAPITAL LETTER U WITH RING ABOVE
0168;Utilde;LATIN CAPITAL LETTER U WITH TILDE
0056;V;LATIN CAPITAL LETTER V
0057;W;LATIN CAPITAL LETTER W
1E82;Wacute;LATIN CAPITAL LETTER W WITH ACUTE
0174;Wcircumflex;LATIN CAPITAL LETTER W WITH CIRCUMFLEX
1E84;Wdieresis;LATIN CAPITAL LETTER W WITH DIAERESIS
1E80;Wgrave;LATIN CAPITAL LETTER W WITH GRAVE
0058;X;LATIN CAPITAL LETTER X
039E;Xi;GREEK CAPITAL LETTER XI
0059;Y;LATIN CAPITAL LETTER Y
00DD;Yacute;LATIN CAPITAL LETTER Y WITH ACUTE
0176;Ycircumflex;LATIN CAPITAL LETTER Y WITH CIRCUMFLEX
0178;Ydieresis;LATIN CAPITAL LETTER Y WITH DIAERESIS
1EF2;Ygrave;LATIN CAPITAL LETTER Y WITH GRAVE
005A;Z;LATIN CAPITAL LETTER Z
0179;Zacute;LATIN CAPITAL LETTER Z WITH ACUTE
017D;Zcaron;LATIN CAPITAL LETTER Z WITH CARON
017B;Zdotaccent;LATIN CAPITAL LETTER Z WITH DOT ABOVE
0396;Zeta;GREEK CAPITAL LETTER ZETA
0061;a;LATIN SMALL LETTER A
00E1;aacute;LATIN SMALL LETTER A WITH ACUTE
0103;abreve;LATIN SMALL LETTER A WITH BREVE
00E2;acircumflex;LATIN SMALL LETTER A WITH CIRCUMFLEX
00B4;acute;ACUTE ACCENT
0301;acutecomb;COMBINING ACUTE ACCENT
00E4;adieresis;LATIN SMALL LETTER A WITH DIAERESIS
00E6;ae;LATIN SMALL LETTER AE
01FD;aeacute;LATIN SMALL LETTER AE WITH ACUTE
00E0;agrave;LATIN SMALL LETTER A WITH GRAVE
2135;aleph;ALEF SYMBOL
03B1;alpha;GREEK SMALL LETTER ALPHA
03AC;alphatonos;GREEK SMALL LETTER ALPHA WITH TONOS
0101;amacron;LATIN SMALL LETTER A WITH MACRON
0026;ampersand;AMPERSAND
2220;angle;ANGLE
2329;angleleft;LEFT-POINTING ANGLE BRACKET
232A;angleright;RIGHT-POINTING ANGLE BRACKET
0387;anoteleia;GREEK ANO TELEIA
0105;aogonek;LATIN SMALL LETTER A WITH OGONEK
2248;approxequal;ALMOST EQUAL TO
00E5;aring;LATIN SMALL LETTER A WITH RING ABOVE
01FB;aringacute;LATIN SMALL LETTER A WITH RING ABOVE AND ACUTE
2194;arrowboth;LEFT RIGHT ARROW
21D4;arrowdblboth;LEFT RIGHT DOUBLE ARROW
21D3;arrowdbldown;DOWNWARDS DOUBLE ARROW
21D0;arrowdblleft;LEFTWARDS DOUBLE ARROW
21D2;arrowdblright;RIGHTWARDS DOUBLE ARROW
21D1;arrowdblup;UPWARDS DOUBLE ARROW
2193;arrowdown;DOWNWARDS ARROW
2190;arrowleft;LEFTWARDS ARROW
2192;arrowright;RIGHTWARDS ARROW
2191;arrowup;UPWARDS ARROW
2195;arrowupdn;UP DOWN ARROW
21A8;arrowupdnbse;UP DOWN ARROW WITH BASE
005E;asciicircum;CIRCUMFLEX ACCENT
007E;asciitilde;TILDE
002A;asterisk;ASTERISK
2217;asteriskmath;ASTERISK OPERATOR
0040;at;COMMERCIAL AT
00E3;atilde;LATIN SMALL LETTER A WITH TILDE
0062;b;LATIN SMALL LETTER B
005C;backslash;REVERSE SOLIDUS
007C;bar;VERTICAL LINE
03B2;beta;GREEK SMALL LETTER BETA
2588;block;FULL BLOCK
007B;braceleft;LEFT CURLY BRACKET
007D;braceright;RIGHT CURLY BRACKET
005B;bracketleft;LEFT SQUARE BRACKET
005D;bracketright;RIGHT SQUARE BRACKET
02D8;breve;BREVE
00A6;brokenbar;BROKEN BAR
2022;bullet;BULLET
0063;c;LATIN SMALL LETTER C
0107;cacute;LATIN SMALL LETTER C WITH ACUTE
02C7;caron;CARON
21B5;carriagereturn;DOWNWARDS ARROW WITH CORNER LEFTWARDS
010D;ccaron;LATIN SMALL LETTER C WITH CARON
00E7;ccedilla;LATIN SMALL LETTER C WITH CEDILLA
0109;ccircumflex;LATIN SMALL LETTER C WITH CIRCUMFLEX
010B;cdotaccent;LATIN SMALL LETTER C WITH DOT ABOVE
00B8;cedilla;CEDILLA
00A2;cent;CENT SIGN
03C7;chi;GREEK SMALL LETTER CHI
25CB;circle;WHITE CIRCLE
2297;circlemultiply;CIRCLED TIMES
2295;circleplus;CIRCLED PLUS
02C6;circumflex;MODIFIER LETTER CIRCUMFLEX ACCENT
2663;club;BLACK CLUB SUIT
003A;colon;COLON
20A1;colonmonetary;COLON SIGN
002C;comma;COMMA
2245;congruent;APPROXIMATELY EQUAL TO
00A9;copyright;COPYRIGHT SIGN
00A4;currency;CURRENCY SIGN
0064;d;LATIN SMALL LETTER D
2020;dagger;DAGGER
2021;daggerdbl;DOUBLE DAGGER
010F;dcaron;LATIN SMALL LETTER D WITH CARON
0111;dcroat;LATIN SMALL LETTER D WITH STROKE
00B0;degree;DEGREE SIGN
03B4;delta;GREEK SMALL LETTER DELTA
2666;diamond;BLACK DIAMOND SUIT
00A8;dieresis;DIAERESIS
0385;dieresistonos;GREEK DIALYTIKA TONOS
00F7;divide;DIVISION SIGN
2593;dkshade;DARK SHADE
2584;dnblock;LOWER HALF BLOCK
0024;dollar;DOLLAR SIGN
20AB;dong;DONG SIGN
02D9;dotaccent;DOT ABOVE
0323;dotbelowcomb;COMBINING DOT BELOW
0131;dotlessi;LATIN SMALL LETTER DOTLESS I
22C5;dotmath;DOT OPERATOR
0065;e;LATIN SMALL LETTER E
00E9;eacute;LATIN SMALL LETTER E WITH ACUTE
0115;ebreve;LATIN SMALL LETTER E WITH BREVE
011B;ecaron;LATIN SMALL LETTER E WITH CARON
00EA;ecircumflex;LATIN SMALL LETTER E WITH CIRCUMFLEX
00EB;edieresis;LATIN SMALL LETTER E WITH DIAERESIS
0117;edotaccent;LATIN SMALL LETTER E WITH DOT ABOVE
00E8;egrave;LATIN SMALL LETTER E WITH GRAVE
0038;eight;DIGIT EIGHT
2208;element;ELEMENT OF
2026;ellipsis;HORIZONTAL ELLIPSIS
0113;emacron;LATIN SMALL LETTER E WITH MACRON
2014;emdash;EM DASH
2205;emptyset;EMPTY SET
2013;endash;EN DASH
014B;eng;LATIN SMALL LETTER ENG
0119;eogonek;LATIN SMALL LETTER E WITH OGONEK
03B5;epsilon;GREEK SMALL LETTER EPSILON
03AD;epsilontonos;GREEK SMALL LETTER EPSILON WITH TONOS
003D;equal;EQUALS SIGN
2261;equivalence;IDENTICAL TO
212E;estimated;ESTIMATED SYMBOL
03B7;eta;GREEK SMALL LETTER ETA
03AE;etatonos;GREEK SMALL LETTER ETA WITH TONOS
00F0;eth;LATIN SMALL LETTER ETH
0021;exclam;EXCLAMATION MARK
203C;exclamdbl;DOUBLE EXCLAMATION MARK
00A1;exclamdown;INVERTED EXCLAMATION MARK
2203;existential;THERE EXISTS
0066;f;LATIN SMALL LETTER F
2640;female;FEMALE SIGN
2012;figuredash;FIGURE DASH
25A0;filledbox;BLACK SQUARE
25AC;filledrect;BLACK RECTANGLE
0035;five;DIGIT FIVE
215D;fiveeighths;VULGAR FRACTION FIVE EIGHTHS
0192;florin;LATIN SMALL LETTER F WITH HOOK
0034;four;DIGIT FOUR
2044;fraction;FRACTION SLASH
20A3;franc;FRENCH FRANC SIGN
0067;g;LATIN SMALL LETTER G
03B3;gamma;GREEK SMALL LETTER GAMMA
011F;gbreve;LATIN SMALL LETTER G WITH BREVE
01E7;gcaron;LATIN SMALL LETTER G WITH CARON
011D;gcircumflex;LATIN SMALL LETTER G WITH CIRCUMFLEX
0121;gdotaccent;LATIN SMALL LETTER G WITH DOT ABOVE
00DF;germandbls;LATIN SMALL LETTER SHARP S
2207;gradient;NABLA
0060;grave;GRAVE ACCENT
0300;gravecomb;COMBINING GRAVE ACCENT
003E;greater;GREATER-THAN SIGN
2265;greaterequal;GREATER-THAN OR EQUAL TO
00AB;guillemotleft;LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
00BB;guillemotright;RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
2039;guilsinglleft;SINGLE LEFT-POINTING ANGLE QUOTATION MARK
203A;guilsinglright;SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
0068;h;LATIN SMALL LETTER H
0127;hbar;LATIN SMALL LETTER H WITH STROKE
0125;hcircumflex;LATIN SMALL LETTER H WITH CIRCUMFLEX
2665;heart;BLACK HEART SUIT
0309;hookabovecomb;COMBINING HOOK ABOVE
2302;house;HOUSE
02DD;hungarumlaut;DOUBLE ACUTE ACCENT
002D;hyphen;HYPHEN-MINUS
0069;i;LATIN SMALL LETTER I
00ED;iacute;LATIN SMALL LETTER I WITH ACUTE
012D;ibreve;LATIN SMALL LETTER I WITH BREVE
00EE;icircumflex;LATIN SMALL LETTER I WITH CIRCUMFLEX
00EF;idieresis;LATIN SMALL LETTER I WITH DIAERESIS
00EC;igrave;LATIN SMALL LETTER I WITH GRAVE
0133;ij;LATIN SMALL LIGATURE IJ
012B;imacron;LATIN SMALL LETTER I WITH MACRON
221E;infinity;INFINITY
222B;integral;INTEGRAL
2321;integralbt;BOTTOM HALF INTEGRAL
2320;integraltp;TOP HALF INTEGRAL
2229;intersection;INTERSECTION
25D8;invbullet;INVERSE BULLET
25D9;invcircle;INVERSE WHITE CIRCLE
263B;invsmileface;BLACK SMILING FACE
012F;iogonek;LATIN SMALL LETTER I WITH OGONEK
03B9;iota;GREEK SMALL LETTER IOTA
03CA;iotadieresis;GREEK SMALL LETTER IOTA WITH DIALYTIKA
0390;iotadieresistonos;GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
03AF;iotatonos;GREEK SMALL LETTER IOTA WITH TONOS
0129;itilde;LATIN SMALL LETTER I WITH TILDE
006A;j;LATIN SMALL LETTER J
0135;jcircumflex;LATIN SMALL LETTER J WITH CIRCUMFLEX
006B;k;LATIN SMALL LETTER K
03BA;kappa;GREEK SMALL LETTER KAPPA
0138;kgreenlandic;LATIN SMALL LETTER KRA
006C;l;LATIN SMALL LETTER L
013A;lacute;LATIN SMALL LETTER L WITH ACUTE
03BB;lambda;GREEK SMALL LETTER LAMDA
013E;lcaron;LATIN SMALL LETTER L WITH CARON
0140;ldot;LATIN SMALL LETTER L WITH MIDDLE DOT
003C;less;LESS-THAN SIGN
2264;lessequal;LESS-THAN OR EQUAL TO
258C;lfblock;LEFT HALF BLOCK
20A4;lira;LIRA SIGN
2227;logicaland;LOGICAL AND
00AC;logicalnot;NOT SIGN
2228;logicalor;LOGICAL OR
017F;longs;LATIN SMALL LETTER LONG S
25CA;lozenge;LOZENGE
0142;lslash;LATIN SMALL LETTER L WITH STROKE
2591;ltshade;LIGHT SHADE
006D;m;LATIN SMALL LETTER M
00AF;macron;MACRON
2642;male;MALE SIGN
2212;minus;MINUS SIGN
2032;minute;PRIME
00B5;mu;MICRO SIGN
00D7;multiply;MULTIPLICATION SIGN
266A;musicalnote;EIGHTH NOTE
266B;musicalnotedbl;BEAMED EIGHTH NOTES
006E;n;LATIN SMALL LETTER N
0144;nacute;LATIN SMALL LETTER N WITH ACUTE
0149;napostrophe;LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
0148;ncaron;LATIN SMALL LETTER N WITH CARON
0039;nine;DIGIT NINE
2209;notelement;NOT AN ELEMENT OF
2260;notequal;NOT EQUAL TO
2284;notsubset;NOT A SUBSET OF
00F1;ntilde;LATIN SMALL LETTER N WITH TILDE
03BD;nu;GREEK SMALL LETTER NU
0023;numbersign;NUMBER SIGN
006F;o;LATIN SMALL LETTER O
00F3;oacute;LATIN SMALL LETTER O WITH ACUTE
014F;obreve;LATIN SMALL LETTER O WITH BREVE
00F4;ocircumflex;LATIN SMALL LETTER O WITH CIRCUMFLEX
00F6;odieresis;LATIN SMALL LETTER O WITH DIAERESIS
0153;oe;LATIN SMALL LIGATURE OE
02DB;ogonek;OGONEK
00F2;ograve;LATIN SMALL LETTER O WITH GRAVE
01A1;ohorn;LATIN SMALL LETTER O WITH HORN
0151;ohungarumlaut;LATIN SMALL LETTER O WITH DOUBLE ACUTE
014D;omacron;LATIN SMALL LETTER O WITH MACRON
03C9;omega;GREEK SMALL LETTER OMEGA
03D6;omega1;GREEK PI SYMBOL
03CE;omegatonos;GREEK SMALL LETTER OMEGA WITH TONOS
03BF;omicron;GREEK SMALL LETTER OMICRON
03CC;omicrontonos;GREEK SMALL LETTER OMICRON WITH TONOS
0031;one;DIGIT ONE
2024;onedotenleader;ONE DOT LEADER
215B;oneeighth;VULGAR FRACTION ONE EIGHTH
00BD;onehalf;VULGAR FRACTION ONE HALF
00BC;onequarter;VULGAR FRACTION ONE QUARTER
2153;onethird;VULGAR FRACTION ONE THIRD
25E6;openbullet;WHITE BULLET
00AA;ordfeminine;FEMININE ORDINAL INDICATOR
00BA;ordmasculine;MASCULINE ORDINAL INDICATOR
221F;orthogonal;RIGHT ANGLE
00F8;oslash;LATIN SMALL LETTER O WITH STROKE
01FF;oslashacute;LATIN SMALL LETTER O WITH STROKE AND ACUTE
00F5;otilde;LATIN SMALL LETTER O WITH TILDE
0070;p;LATIN SMALL LETTER P
00B6;paragraph;PILCROW SIGN
0028;parenleft;LEFT PARENTHESIS
0029;parenright;RIGHT PARENTHESIS
2202;partialdiff;PARTIAL DIFFERENTIAL
0025;percent;PERCENT SIGN
002E;period;FULL STOP
00B7;periodcentered;MIDDLE DOT
22A5;perpendicular;UP TACK
2030;perthousand;PER MILLE SIGN
20A7;peseta;PESETA SIGN
03C6;phi;GREEK SMALL LETTER PHI
03D5;phi1;GREEK PHI SYMBOL
03C0;pi;GREEK SMALL LETTER PI
002B;plus;PLUS SIGN
00B1;plusminus;PLUS-MINUS SIGN
211E;prescription;PRESCRIPTION TAKE
220F;product;N-ARY PRODUCT
2282;propersubset;SUBSET OF
2283;propersuperset;SUPERSET OF
221D;proportional;PROPORTIONAL TO
03C8;psi;GREEK SMALL LETTER PSI
0071;q;LATIN SMALL LETTER Q
003F;question;QUESTION MARK
00BF;questiondown;INVERTED QUESTION MARK
0022;quotedbl;QUOTATION MARK
201E;quotedblbase;DOUBLE LOW-9 QUOTATION MARK
201C;quotedblleft;LEFT DOUBLE QUOTATION MARK
201D;quotedblright;RIGHT DOUBLE QUOTATION MARK
2018;quoteleft;LEFT SINGLE QUOTATION MARK
201B;quotereversed;SINGLE HIGH-REVERSED-9 QUOTATION MARK
2019;quoteright;RIGHT SINGLE QUOTATION MARK
201A;quotesinglbase;SINGLE LOW-9 QUOTATION MARK
0027;quotesingle;APOSTROPHE
0072;r;LATIN SMALL LETTER R
0155;racute;LATIN SMALL LETTER R WITH ACUTE
221A;radical;SQUARE ROOT
0159;rcaron;LATIN SMALL LETTER R WITH CARON
2286;reflexsubset;SUBSET OF OR EQUAL TO
2287;reflexsuperset;SUPERSET OF OR EQUAL TO
00AE;registered;REGISTERED SIGN
2310;revlogicalnot;REVERSED NOT SIGN
03C1;rho;GREEK SMALL LETTER RHO
02DA;ring;RING ABOVE
2590;rtblock;RIGHT HALF BLOCK
0073;s;LATIN SMALL LETTER S
015B;sacute;LATIN SMALL LETTER S WITH ACUTE
0161;scaron;LATIN SMALL LETTER S WITH CARON
015F;scedilla;LATIN SMALL LETTER S WITH CEDILLA
015D;scircumflex;LATIN SMALL LETTER S WITH CIRCUMFLEX
2033;second;DOUBLE PRIME
00A7;section;SECTION SIGN
003B;semicolon;SEMICOLON
0037;seven;DIGIT SEVEN
215E;seveneighths;VULGAR FRACTION SEVEN EIGHTHS
2592;shade;MEDIUM SHADE
03C3;sigma;GREEK SMALL LETTER SIGMA
03C2;sigma1;GREEK SMALL LETTER FINAL SIGMA
223C;similar;TILDE OPERATOR
0036;six;DIGIT SIX
002F;slash;SOLIDUS
263A;smileface;WHITE SMILING FACE
0020;space;SPACE
2660;spade;BLACK SPADE SUIT
00A3;sterling;POUND SIGN
220B;suchthat;CONTAINS AS MEMBER
2211;summation;N-ARY SUMMATION
263C;sun;WHITE SUN WITH RAYS
0074;t;LATIN SMALL LETTER T
03C4;tau;GREEK SMALL LETTER TAU
0167;tbar;LATIN SMALL LETTER T WITH STROKE
0165;tcaron;LATIN SMALL LETTER T WITH CARON
2234;therefore;THEREFORE
03B8;theta;GREEK SMALL LETTER THETA
03D1;theta1;GREEK THETA SYMBOL
00FE;thorn;LATIN SMALL LETTER THORN
0033;three;DIGIT THREE
215C;threeeighths;VULGAR FRACTION THREE EIGHTHS
00BE;threequarters;VULGAR FRACTION THREE QUARTERS
02DC;tilde;SMALL TILDE
0303;tildecomb;COMBINING TILDE
0384;tonos;GREEK TONOS
2122;trademark;TRADE MARK SIGN
25BC;triagdn;BLACK DOWN-POINTING TRIANGLE
25C4;triaglf;BLACK LEFT-POINTING POINTER
25BA;triagrt;BLACK RIGHT-POINTING POINTER
25B2;triagup;BLACK UP-POINTING TRIANGLE
0032;two;DIGIT TWO
2025;twodotenleader;TWO DOT LEADER
2154;twothirds;VULGAR FRACTION TWO THIRDS
0075;u;LATIN SMALL LETTER U
00FA;uacute;LATIN SMALL LETTER U WITH ACUTE
016D;ubreve;LATIN SMALL LETTER U WITH BREVE
00FB;ucircumflex;LATIN SMALL LETTER U WITH CIRCUMFLEX
00FC;udieresis;LATIN SMALL LETTER U WITH DIAERESIS
00F9;ugrave;LATIN SMALL LETTER U WITH GRAVE
01B0;uhorn;LATIN SMALL LETTER U WITH HORN
0171;uhungarumlaut;LATIN SMALL LETTER U WITH DOUBLE ACUTE
016B;umacron;LATIN SMALL LETTER U WITH MACRON
005F;underscore;LOW LINE
2017;underscoredbl;DOUBLE LOW LINE
222A;union;UNION
2200;universal;FOR ALL
0173;uogonek;LATIN SMALL LETTER U WITH OGONEK
2580;upblock;UPPER HALF BLOCK
03C5;upsilon;GREEK SMALL LETTER UPSILON
03CB;upsilondieresis;GREEK SMALL LETTER UPSILON WITH DIALYTIKA
03B0;upsilondieresistonos;GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS
03CD;upsilontonos;GREEK SMALL LETTER UPSILON WITH TONOS
016F;uring;LATIN SMALL LETTER U WITH RING ABOVE
0169;utilde;LATIN SMALL LETTER U WITH TILDE
0076;v;LATIN SMALL LETTER V
0077;w;LATIN SMALL LETTER W
1E83;wacute;LATIN SMALL LETTER W WITH ACUTE
0175;wcircumflex;LATIN SMALL LETTER W WITH CIRCUMFLEX
1E85;wdieresis;LATIN SMALL LETTER W WITH DIAERESIS
2118;weierstrass;SCRIPT CAPITAL P
1E81;wgrave;LATIN SMALL LETTER W WITH GRAVE
0078;x;LATIN SMALL LETTER X
03BE;xi;GREEK SMALL LETTER XI
0079;y;LATIN SMALL LETTER Y
00FD;yacute;LATIN SMALL LETTER Y WITH ACUTE
0177;ycircumflex;LATIN SMALL LETTER Y WITH CIRCUMFLEX
00FF;ydieresis;LATIN SMALL LETTER Y WITH DIAERESIS
00A5;yen;YEN SIGN
1EF3;ygrave;LATIN SMALL LETTER Y WITH GRAVE
007A;z;LATIN SMALL LETTER Z
017A;zacute;LATIN SMALL LETTER Z WITH ACUTE
017E;zcaron;LATIN SMALL LETTER Z WITH CARON
017C;zdotaccent;LATIN SMALL LETTER Z WITH DOT ABOVE
0030;zero;DIGIT ZERO
03B6;zeta;GREEK SMALL LETTER ZETA
#END
"""


AGLError = "AGLError"

AGL2UV = {}
UV2AGL = {}

def _builddicts():
	import re
	
	lines = _aglText.splitlines()
	
	parseAGL_RE = re.compile("([0-9A-F]{4});([A-Za-z_0-9.]+);.*?$")
	
	for line in lines:
		if not line or line[:1] == '#':
			continue
		m = parseAGL_RE.match(line)
		if not m:
			raise AGLError, "syntax error in glyphlist.txt: %s" % repr(line[:20])
		unicode = m.group(1)
		assert len(unicode) == 4
		unicode = int(unicode, 16)
		glyphName = m.group(2)
		if glyphName in AGL2UV:
			# the above table contains identical duplicates
			assert AGL2UV[glyphName] == unicode
		else:
			AGL2UV[glyphName] = unicode
		UV2AGL[unicode] = glyphName
	
_builddicts()
