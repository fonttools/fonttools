import DefaultTable
import array

class table__p_r_e_p(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		self.prep = data
	
	def compile(self, ttFont):
		return self.prep
	
	def __len__(self):
		return len(self.prep)
	
