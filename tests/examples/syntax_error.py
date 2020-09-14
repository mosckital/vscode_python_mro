"""
This module provides examples for tests to check if the language server can
correctly deal with the case that there are syntax errors in the target script.

For example, there may be a good class declaration at the start of the script
followed by a bad class declaration. The language server should be able to
provide MRO information for the good one and no information for the bad one.
"""
from abc import ABC


class GoodClass(ABC):

	def __init__(self) -> None:
		self.val = 0


class BadClass(ABC)

	def __init__()
		self.val = 1