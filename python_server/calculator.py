import jedi
from enum import IntEnum
from typing import Sequence, Tuple
from jedi.api.classes import Name


class MROCalculator(type(Name)):
    """
	This class gathers the methods to calculate the MRO list given a Jedi Name
	representing a class name.
	"""

    @staticmethod
    def get_parent_class_str_from_class_name(name: Name) -> str:
        """
		To fetch the string of the parent class list in the class declaration
		signature from a given class Jedi Name.

		Args:
			name: the given Jedi Name of the target class
		
		Returns:
			the fetched string of the parent class list
		"""
        # check if the given name represents a class
        if name.type != 'class':
            raise ValueError('Should be a jedi Name for class!')
        # get the start and end positions and then the lines between (inclusive)
        start_pos = name.get_definition_start_position()
        end_pos = name.get_definition_end_position()
        lines = name.get_line_code(after=end_pos[0] - start_pos[0]).splitlines()
        # trim the unwanted part in the first and the last lines
        lines[-1] = lines[-1][:end_pos[1]]
        lines[0] = lines[0][start_pos[1]:]
        # join the lines into a single string
        sig_str = (''.join(lines)).split(':')[0]
        # the joined string should start with word `class`
        assert sig_str.startswith('class ')
        # case that no parent class
        if '(' not in sig_str:
            return ""  # no parent class, only 'object'
        # case that having parent classes surrounded by a pair of parentheses
        return sig_str[sig_str.index('(') + 1 : len(sig_str) - 1]

    @staticmethod
    def get_name_at_pos(
			lines: Sequence[str], row: int, col: int
		) -> Tuple[str, int, int]:
        """
		Get the entity name at the given position.

		Args:
			lines: the lines of codes to analyse
			row: the row of the target entity in the given lines
			col: the column of the target entity in the given lines
		
		Returns:
			(the name, the row of the name's end, the column of the name's end)
		"""
        idx = col
		# a name should start with alphabet and continue with alphabet, number
		# or underscore
		# a name should be in the same line, not separated by any other char
        if lines[row][idx].isalpha():
            while lines[row][idx].isalnum() or lines[row][idx] == '_':
                idx += 1
        return lines[row][col:idx], row, idx


class Bracket(IntEnum):

    ROUND = 1
    SQUARE = 2
    CURLY = 3


class ParentClass:

    def __init__(self, name: str, pos: Tuple[int, int]) -> None:
        self.name = name
        self.pos = pos
        self.params : Sequence[Tuple[Bracket, Sequence[ParentClass]]] = None
