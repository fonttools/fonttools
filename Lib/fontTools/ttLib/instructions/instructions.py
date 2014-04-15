#instructions classes are generated from instructionList
class root_instruct(object):
    def __init__(self):
	self.data = []
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def prettyPrinter(self):
        print(self.__class__.__name__,self.data)
class all():
    class PUSH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 
    class AA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class ABS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class ADD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class ALIGNPTS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class ALIGNRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class AND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class CALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class CEILING(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class CINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class CLEAR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DEBUG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class DELTAC1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DELTAC2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DELTAC3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DELTAP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DELTAP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DELTAP3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class DEPTH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class DIV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class DUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class EIF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class ELSE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class ENDF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class EQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class EVEN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class FDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class FLIPOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class FLIPON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class FLIPPT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class FLIPRGOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class FLIPRGON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class FLOOR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class GC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class GETINFO(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class GFV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class GPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class GT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class GTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class IDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class IF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class INSTCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class IP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class ISECT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  5 
        def action(self, space):
            pass 

    class IUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class JMPR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class JROF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class JROT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class LOOPCALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class LT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class LTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MAX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MDAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class MDRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class MIAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MIN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class MIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MPPEM(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class MPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class MSIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class MUL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class NEG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class NEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class NOT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class NROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class ODD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class OR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class POP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class RCVT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class RDTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class ROFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class ROLL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  3 
            self.pop_num =  3 
        def action(self, space):
            pass 

    class ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class RS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class RTDG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class RTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class RTHG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class RUTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class S45ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SANGW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SCANCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SCANTYPE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SCFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SCVTCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SDB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SDPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SDS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SFVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SFVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class SFVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SFVTPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class SHC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SHP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class SHPIX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self, space):
            pass 

    class SHZ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SLOOP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SMD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SPVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SPVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class SPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SRP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SRP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SRP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SSW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SSWCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SUB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self, space):
            pass 

    class SWAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class SZP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SZP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SZP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class SZPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class UTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self, space):
            pass 

    class WCVTF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class WCVTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

    class WS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self, space):
            pass 

