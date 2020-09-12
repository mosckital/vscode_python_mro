"""
This module provides examples for tests to check if the word class in docstring,
end-of-line comment, multi-line comment or string literals are correctly ignored
by the language server.

Unnecessary class word, ABC, WordInComments
"""
from abc import ABC, abstractmethod  # unnecessary class word, ABC


class WordInComments(ABC):  # unnecessary class word, ABC, WordInComments
	"""
	This class, WordInComments, is an example class definition for testing if
	the class word and name can be correctly ignored by the language server.
	"""

	STATIC_VAL = 'class word, ABC, WordInComments'
	"""Unnecessary class word, ABC, WordInComments"""

	@property  # unnecessary class word, ABC, WordInComments
	@abstractmethod  # unnecessary class word, ABC, WordInComments
	def property_1(self):  # unnecessary class word, ABC, WordInComments
		"""Unnecessary class word, ABC, WordInComments"""
		# unnecessary class word, ABC, WordInComments
		pass  # unnecessary class word, ABC, WordInComments

	@staticmethod  # unnecessary class word, ABC, WordInComments
	def static_1():  # unnecessary class word, ABC, WordInComments
		pass

	@classmethod  # unnecessary class word, ABC, WordInComments
	def class_1(cls):  # unnecessary class word, ABC, WordInComments
		pass

	@classmethod
	def class_2(_class):  # unnecessary class word, ABC, WordInComments
		"""
		Unnecessary class word,
		ABC, WordInComments
		"""
		pass

	def method_1(
		self,  # unnecessary class word, ABC, WordInComments
		val_1: \
			str,  # unnecessary class word, ABC, WordInComments
		val_2: int,
	):  # unnecessary class word, ABC, WordInComments
		pass


class MultiLineDef(  # unnecessary class word, ABC, WordInComments
	WordInComments,  # unnecessary class word, ABC, WordInComments
):  # unnecessary class word, ABC, WordInComments
	pass


class DefInComments(
	MultiLineDef,  # class TestDef: pass
):  # class TestDef: pass
	"""
	class TestDef:
		pass
	"""

	VAL = "class TestDef: pass"
	"""class TestDef: pass"""

"""
Unnecessary multi-line at the end of file with out a new empty line for ending.
This aims to test if the language server can deal with this non-recommended end.
"""