from __future__ import annotations
from _pytest.mark import param
import jedi
from typing import Sequence, Tuple, List, Optional
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
    def get_parent_class_list(name: Name) -> Sequence[Tuple[str, int, int]]:
        """
        Get the list of the parent class information from the given class' Jedi
        Name.

        Args:
            name: the given Jedi Name of the target class

        Returns:
            a list of the parent class information in format of tuple
            (class name, line number in script, column number in script),
            where the line number is starting with 1, conforming Jedi standard
        """
        # check if the given name represents a class
        if name.type != 'class':
            raise ValueError('Should be a jedi Name for class!')
        # get the start and end positions and then the lines between (inclusive)
        start_pos = name.get_definition_start_position()
        end_pos = name.get_definition_end_position()
        lines = name.get_line_code(after=end_pos[0] - start_pos[0]).splitlines()
        # resolve the class signature of the given class name
        # extract_next() requires the first line of the input has the index 0
        line_offset = start_pos[0]
        target_class, _, _ = ParentClass.extract_next(lines, 0, start_pos[1])
        if target_class.params:
            # a valid class signature should have at most one set of parent
            # classes surrounded by parentheses
            return [
                # adding back the line offset
                (parent.name, parent.pos[0] + line_offset, parent.pos[0])
                for parent in target_class.params[0][1]
            ]
        else:
            # case of no parent class
            return []

    @staticmethod
    def get_name_at_pos(
            line: str, char: int
        ) -> Tuple[str, int]:
        """
        Get the entity name at the given position.

        Args:
            line: the line to analyse
            char: the index of starting character of the name
        
        Returns:
            (the name, the index of the character after the name)
        """
        idx = char
        # a name should start with alphabet and continue with alphabet, number
        # or underscore
        # a name should be in the same line, not separated by any other char
        if line[idx].isalpha():
            while line[idx].isalnum() or line[idx] == '_':
                idx += 1
        return line[char:idx], idx

    @staticmethod
    def ignore_non_parentheses(
            lines: Sequence[str], n_row: int, n_col: int, hard_stop: str = ':'
        ) -> Tuple[int, int]:
        """
        To ignore and skip the non-parentheses and non-variable-name characters
        starting from the given position until the first meeting parentheses or
        variable-name character.

        Args:
            lines: the lines of the code block
            n_row: the index of the starting row
            n_col: the index of the starting column
            hard_stop: the character which will stop the processing in any case
        """
        while n_row < len(lines) and n_col < len(lines[n_row]):
            char = lines[n_row][n_col]
            if char.isalnum() or char == '_' or \
                char in BRACKETS or char in BRACKETS.values() or \
                char == hard_stop:
                # termination situation
                break
            if char in ['#', '\n', '\\']:
                # deal with advancing to new line situation
                n_row, n_col = n_row + 1, 0
            else:
                n_col += 1
        return n_row, n_col


BRACKETS = {
    '(': ')',
    '[': ']',
    '{': '}',
}
"""All brackets in a dictionary."""


class ParentClass:
    """The class encapsulates the parent classes in class declaration signature
    and a syntax analysis function.
    """

    def __init__(self, name: str, pos: Tuple[int, int]) -> None:
        self.name = name  # the name of the class
        self.pos = pos  # the (line, column) in the script (Jedi standard)
        # the list of parameters like generic type or function param
        # it may have multiple lists of parameters (very very rare)
        # each list is in format of (parentheses char, param list)
        self.params : List[Tuple[str, Sequence[ParentClass]]] = []

    @staticmethod
    def extract_next(
            lines: Sequence[str], n_row: int, n_col: int, hard_stop: str = ':'
        ) -> Tuple[Optional[ParentClass], int, int]:
        """
        Extract the next ParentClass.

        Args:
            lines: the lines of relevant codes
            n_row: the line of the starting position
            n_col: the column of the starting position
            hard_stop: the character which will stop the processing in any case
        
        Returns:
            (the extracted ParentClass or None, the line of the character after
            ending position, the column of the character after ending position)
        """
        # skip all non parentheses
        n_row, n_col = MROCalculator.ignore_non_parentheses(lines, n_row, n_col)
        # case of nothing to extract
        if lines[n_row][n_col] == hard_stop:
            return None, n_row, n_col
        # extract the basic name and position
        parent_pos_col = n_col
        parent_name, n_col = MROCalculator.get_name_at_pos(lines[n_row], n_col)
        parent = ParentClass(parent_name, (n_row, parent_pos_col))
        # to extract the param lists
        bra, ket, params = '', '', []
        while n_row < len(lines) and n_col < len(lines[n_row]) and \
            lines[n_row][n_col] != hard_stop:
            if not bra:
                # case of opening a new param list
                bra = lines[n_row][n_col]
                ket = BRACKETS[bra]
                n_col += 1
                if n_col == len(lines[n_row]):
                    n_row, n_col = n_row + 1, 0
            elif lines[n_row][n_col] == ket:
                # case of closing a param list and save it
                parent.params.append((bra, params))
                bra, ket, params = '', '', []
                n_col += 1
                if n_col == len(lines[n_row]):
                    n_row, n_col = n_row + 1, 0
            else:
                # case of filling the current param list
                n_row, n_col = MROCalculator.ignore_non_parentheses(lines, n_row, n_col)
                param, n_row, n_col = ParentClass.extract_next(lines, n_row, n_col)
                params.append(param)
        return parent, n_row, n_col
