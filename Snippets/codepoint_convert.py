__author__ = 'bihiceng@gmail.com'

from gbk import from_uni, to_uni

def convert_to_gbk(uni_code):
    page = from_uni[(uni_code >> 8) & 0xFF];
    return 0x3F if page is None else page[uni_code & 0xFF]

def convert_from_gbk(gbk_code):
    page = to_uni[(gbk_code >> 8) & 0xFF];
    return 0xFFFE if page is  None else page[gbk_code & 0xFF]

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Please input a gbk code point')
        sys.exit(1)
    u = convert_from_gbk(int(sys.argv[1]))
    print (u)
