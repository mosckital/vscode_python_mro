import ast
import jedi
from typing import Tuple, Sequence
from jedi.api import Script
from jedi.api.classes import Name
from python_server.parsed_class import ParsedClass


class ParsedCustomClass(ParsedClass):
    """
    This class encapsulates a class definition parsed for MRO list calculation
    and all the intermediate results during the calculation.

    All the necessary calculation to get the MRO list will be done during the
    initialisation of the instance.
    """

    OBJECT_CLASS : Name = jedi.Script(code='object').infer(1, 0)[0]

    def __init__(self, jedi_name: Name, jedi_script: Script) -> None:
        super().__init__(jedi_name)
        self._jedi_script = jedi_script
        self._lines = self._get_code_lines()
        self._class_def = self._get_class_def_ast_from_lines()
        if self.jedi_name.line is None or self.jedi_name.column is None:
            raise ValueError(f'Parsed class {self.jedi_name.full_name} has no line or column information.')
        # positions with line starting with 1 (Jedi and AST standard)
        self.start_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column
        )
        self.end_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column + len(self._class_def.name)
        )
        self._base_parent_names : Sequence[Name] = [
            self._jedi_script.infer(
                b.lineno + self.jedi_name.line - 1,
                b.col_offset
            )[0]
            for b in self._class_def.bases
        ]
        self.mro_name_list = self._get_mro_name_list()
        self.code_lens = self.get_code_lens()

    def _get_code_lines(self):
        """Get the code block of the class definition, separated by lines."""
         # get the start and end positions and then the lines between (inclusive)
        start_pos = self.jedi_name.get_definition_start_position()
        end_pos = self.jedi_name.get_definition_end_position()
        lines = self.jedi_name.get_line_code(
            after=end_pos[0] - start_pos[0]
        ).splitlines()
        # trim the unwanted part in the first and the last lines
        # trim the last line first, otherwise the end position can be corrupted
        # when there is only one line
        lines[-1] = lines[-1][:end_pos[1]]
        lines[0] = lines[0][start_pos[1]:]
        return lines
    
    def _get_class_def_ast_from_lines(self):
        """Get the correspondent ast.ClassDef instance."""
        codes = '\n'.join(self._lines)
        mod = ast.parse(codes)
        # there will be one and only one class definition
        return [n for n in mod.body if isinstance(n, ast.ClassDef)][0]
    
    def _get_mro_name_list(self) -> Sequence[Name]:
        """Calculate the MRO list in Jedi Name."""
        return self._base_parent_names