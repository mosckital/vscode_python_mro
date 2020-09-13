"""
This module provies examples for tests to check if a class declaration in
docstring, end-of-line comment, multi-line comment or string literals are
correctly ignored by the language server.
"""
from abc import ABC, abstractmethod  # class Ignore: pass


class DefinitionInComments(
	ABC  # class Ignore(ABC): pass
):
	"""The following class declaration should be ignored:

	class Ignore(ABC):
		
		def __init__(self):
			self.val = 1
	
	The above class declaration should be ignored.
	"""

	@abstractmethod  # class Ignore: pass
	def method(self):
		"""
		class Ignore(ABC):

			@property
			def val(self):
				return 1
		"""
		# the above class declaration should be ignored
		class_def = 'class Ignore: pass'
		return class_def  # class Ignore: pass
	
	STATIC_VAL = """

class Ignore(ABC):

	def should_ignore(self):
		return True

"""