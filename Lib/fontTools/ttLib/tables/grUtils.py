import struct, warnings
try:
    import lz4
except: 
    lz4 = None

#old scheme for VERSION < 0.9 otherwise use lz4.block

def decompress(data):
    (compression,) = struct.unpack(">L", data[4:8])
    scheme = compression >> 27
    size = compression & 0x07ffffff
    if scheme == 0:
        pass
    elif scheme == 1 and lz4:
        res = lz4.decompress(struct.pack("<L", size) + data[8:])
        if len(res) != size:
            warnings.warn("Table decompression failed.")
        else:
            data = res
    else:
        warnings.warn("Table is compressed with an unsupported compression scheme")
    return (data, scheme)

def compress(scheme, data):
    hdr = data[:4] + struct.pack(">L", (scheme << 27) + (len(data) & 0x07ffffff))
    if scheme == 0 :
        return data
    elif scheme == 1 and lz4:
        res = lz4.compress(hdr + data)
        return res
    else:
        warnings.warn("Table failed to compress by unsupported compression scheme")
    return data

def _entries(attrs, sameval):
    ak = 0
    vals = []
    lastv = 0
    for k,v in attrs:
        if len(vals) and (k != ak + 1 or (sameval and v != lastv)) :
            yield (ak - len(vals) + 1, len(vals), vals)
            vals = []
        ak = k
        vals.append(v)
        lastv = v
    yield (ak - len(vals) + 1, len(vals), vals)

def entries(attributes, sameval = False):
    g = _entries(sorted(attributes.iteritems(), key=lambda x:int(x[0])), sameval)
    return g

def bininfo(num, size=1):
    if num == 0:
        return struct.pack(">4H", 0, 0, 0, 0)
    srange = 1;
    select = 0
    while srange <= num:
        srange *= 2
        select += 1
    select -= 1
    srange /= 2
    srange *= size
    shift = num * size - srange
    return struct.pack(">4H", num, srange, select, shift)

def num2tag(n):
    if n < 0x200000:
        return str(n)
    else:
        return struct.unpack('4s', struct.pack('>L', n))[0].replace('\000', '')

def tag2num(n):
    try:
        return int(n)
    except ValueError:
        n = (n+"    ")[:4]
        return struct.unpack('>L', n)[0]

