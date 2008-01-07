class ScriptTag(BaseTag):

	"""Tag that contains Javascript code."""
	
	def __init__(self, parent, attrs):
		BaseTag.__init__(self, parent, attrs)
		
	def _emit(self, page, target=None):
		page.scripts.append(content(self))


class PHPTag(BaseTag):

	"""Tag that contains php code.
	Automatically sets the extension of the final file to .php
	"""
	
	def __init__(self, parent, attrs):
		BaseTag.__init__(self, parent, attrs)
		
	def _emit(self, page, target=None):
		target.append("<?php %s ?>"%content(self))
