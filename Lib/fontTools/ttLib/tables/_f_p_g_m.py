import DefaultTable
import array

class table__f_p_g_m(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		self.fpgm = data
	
	def compile(self, ttFont):
		return self.fpgm
	
	def __len__(self):
		return len(self.fpgm)
	
