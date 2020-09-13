"""
This module provides examples for tests to check if a class declaration with a
lot of unnecessary spaces, new lines, change-of-line or comments between
keywords or brackets can be successfully detected by the language server.
"""
from abc import ABC


class TwistedDeclaration\
									\
									(  # strange change line and new line
										ABC\
											
											# strange comment
)\
	:

	# unnecessary space

	def\
			__init__\
				(
					\
					
						


		self
		\
			\
) -> \
	None\
:
			self\
				.\
		val = \
			\
(
			1,2,       \
	3
	,
\
		)
			
			val2\
						=\
								[
									# strange comments
									'car'      ,

									"""
						


									""",

f''
								]