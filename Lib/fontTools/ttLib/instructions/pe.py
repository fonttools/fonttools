class ProgramEnvironment(object):
	def __init__(self,state=None,stack=None,function_table=None,cvt_table=None,whole_program_status=None):
		#state 1 means exectue instruction,2 means pushing data
		self.state = 1
		self.stack = []
		self.whole_program_status = True
		self.function_table = {}
		self.cvt_table = {}
	