from fontTools import ttLib

superclass = ttLib.getTableClass("TSI1")

class table_T_S_I__3(superclass):
	
	extras = {0xfffa: "reserved0", 0xfffb: "reserved1", 0xfffc: "reserved2", 0xfffd: "reserved3"}
	
	indextable = "TSI2"


