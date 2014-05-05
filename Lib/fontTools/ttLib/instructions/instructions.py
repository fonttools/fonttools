#instructions classes are generated from instructionList
class root_instruct(object):
    def __init__(self):
	self.data = []
        self.successor = None 
        self.top = None
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def set_top(self,value):
        self.top = value
    def get_pop_num(self):
        return self.pop_num
    def get_push_num(self):
        return self.push_num
    def set_input(self,data):
        self.data = data
    def get_successor(self):
        return self.successor
    def set_successor(self,successor):
        self.successor = successor
    def get_result(self):
        return self.data
    def prettyPrinter(self):
        print(self.__class__.__name__,self.data,self.top)
class all():
    class PUSH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self)
            self.push_num = len(self.data)
            self.pop_num = 0
        def get_push_num(self):
            return len(self.data)
        def action(self):
            pass 

    class AA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class ABS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class ADD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class ALIGNPTS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class ALIGNRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class AND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class CALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class CEILING(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class CINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class CLEAR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DEBUG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class DELTAC1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DELTAC2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DELTAC3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DELTAP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DELTAP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DELTAP3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class DEPTH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self):
            pass 

    class DIV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class DUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  1 
        def action(self):
            pass 

    class EIF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class ELSE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class ENDF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class EQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class EVEN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class FDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class FLIPOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class FLIPON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class FLIPPT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class FLIPRGOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class FLIPRGON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class FLOOR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class GC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class GETINFO(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class GFV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  0 
        def action(self):
            pass 

    class GPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  0 
        def action(self):
            pass 

    class GT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class GTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class IDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class IF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class INSTCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class IP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class ISECT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  5 
        def action(self):
            pass 

    class IUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class JMPR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class JROF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class JROT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class LOOPCALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class LT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class LTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class MAX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class MD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class MDAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class MDRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class MIAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class MIN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class MINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class MIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class MPPEM(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self):
            pass 

    class MPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  0 
        def action(self):
            pass 

    class MSIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class MUL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class NEG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class NEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class NOT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class NROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class ODD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class OR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class POP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class RCVT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class RDTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class ROFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class ROLL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  3 
            self.pop_num =  3 
        def action(self):
            pass 

    class ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class RS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  1 
        def action(self):
            pass 

    class RTDG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class RTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class RTHG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class RUTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class S45ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SANGW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SCANCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SCANTYPE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SCFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SCVTCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SDB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SDPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SDS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SFVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SFVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class SFVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SFVTPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class SHC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SHP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class SHPIX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  -1 
        def action(self):
            pass 

    class SHZ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SLOOP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SMD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SPVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SPVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class SPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class SROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SRP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SRP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SRP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SSW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SSWCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SUB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  1 
            self.pop_num =  2 
        def action(self):
            pass 

    class SVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  0 
        def action(self):
            pass 

    class SWAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  2 
            self.pop_num =  2 
        def action(self):
            pass 

    class SZP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SZP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SZP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class SZPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class UTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  1 
        def action(self):
            pass 

    class WCVTF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class WCVTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

    class WS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.push_num =  0 
            self.pop_num =  2 
        def action(self):
            pass 

