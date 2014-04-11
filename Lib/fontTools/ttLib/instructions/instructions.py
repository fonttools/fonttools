from pstates import States as states
class root_instruct(object):
    def __init__(self):
	self.data = []
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def prettyPrinter(self):
        #TODO:implement printy printer
        print(self.__class__,self.data)
class all():

    class PUSH(root_instruct):
        def action(self,data = None):
        	pass
       	'''
	    if self.programe_env.state == states.normal:
	        print "program state to 2"
		self.programe_env.state = states.push_data
	    else :
		if self.programe_env.state == states.push_data:
		    print "begin pushing data"
	            for data_ele in data:
		        print data_ele
			self.PushStack(data_ele)
		'''
    class DUP(root_instruct):
        def action(self):
	    print "DUP takes action"
	    self.PushStack(self.top())
    class FDEF(root_instruct):
        def action(self):
	    print "FDEF takes action"
	    self.programe_env.function_table[self.top()] = self.programe_env.stack
    class ELSE(root_instruct):
	def action(self):
	    pass
    class ENDF(root_instruct):
	def action(self):
	    pass
    class AND(root_instruct):
	def action(self):
	    op1 = self.top()
	    pop()
	    op2 = top()
	    pop()

    class CALL(root_instruct):
	def action(self):
	    pass
    class CEILING(root_instruct):
	def action(self):
	    pass
    class CINDEX(root_instruct):
	def action(self):
	    pass
    class CLEAR(root_instruct):
	def action(self):
	    pass
    class ADD(root_instruct):
	def action(self):
	    pass
    class SUB(root_instruct):
	def action(self):
	    pass
    class SWAP(root_instruct):
	def action(self):
	    pass
    class RCVT(root_instruct):
	def action(self):
	    pass

  	
    class WCVTP(root_instruct):
   	def action(self):
	    pass

    class CINDEX(root_instruct):
	def action(self):
	    pass
    class SCFS(root_instruct):
	def action(self):
	    pass
	class MINDEX(root_instruct):
		def action(self):
			pass
	class SWAP(root_instruct):
		def action(self):
			pass
	class ALIGNRP(root_instruct):
		def action(self):
			self.programe_env.state.pop()
			self.programe_env.state.pop()
			pass
	class ALIGNPTS(root_instruct):
		def action(self):
			pass
		
	class LTEQ(root_instruct):
		def action(self):
			pass
	class IF(root_instruct):
		def action(self):
			pass
	class POP(root_instruct):
		def action(self):
			pass
	class RS(root_instruct):
		def action(self):
			pass
	class NEG(root_instruct):
		def action(self):
			pass
	class SROUND(root_instruct):
		def action(self):
			pass
	class ROLL(root_instruct):
		def action(self):
			pass
	class AA(root_instruct):
		def action(self):
			pass
	class ABS(root_instruct):
		def action(self):
			pass
	class GT(root_instruct):
		def action(self):
			pass
	class RTG(root_instruct):
		def action(self):
			pass
	class EIF(root_instruct):
		def action(self):
			pass
	class SPVFS(root_instruct):
		def action(self):
			pass
	class SFVFS(root_instruct):
		def action(self):
			pass
	class WCVTF(root_instruct):
		def action(self):
			pass
	class GFV(root_instruct):
		def action(self):
			pass
	class MAX(root_instruct):
		def action(self):
			pass
	class MIN(root_instruct):
		def action(self):
			pass
	class MIN(root_instruct):
		def action(self):
			pass


