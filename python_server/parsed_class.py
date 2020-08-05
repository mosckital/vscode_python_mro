import ast
from typing import Tuple, Sequence
from jedi.api import Script
from jedi.api.classes import Name


class ParsedClass:
    """
    This class encapsulates a class definition parsed for MRO list calculation
    and all the intermediate results during the calculation.

    All the necessary calculation to get the MRO list will be done during the
    initialisation of the instance.
    """

    def __init__(self, jedi_name: Name, jedi_script: Script) -> None:
        self.jedi_name = jedi_name
        self.jedi_script = jedi_script
        self.lines = self._get_code_lines()
        self.class_def = self._get_class_def_ast_from_lines()
        if not self.jedi_name.line or not self.jedi_name.column:
            raise ValueError(f'Parsed class {self.jedi_name.full_name} has no line or column information.')
        # positions with line starting with 1 (Jedi and AST standard)
        self.start_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column
        )
        self.end_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column + len(self.class_def.name)
        )
        self.base_parent_info : Sequence[Tuple[Tuple[int, int], Name]] = [
            (
                (b.lineno + self.jedi_name.line - 1, b.col_offset),
                self.jedi_script.infer(
                    b.lineno + self.jedi_name.line - 1,
                    b.col_offset
                )[0]
            )
            for b in self.class_def.bases
        ]
        self.mro_list = self._get_mro_list()
        self.code_lens = self._get_code_lens()

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
        codes = '\n'.join(self.lines)
        mod = ast.parse(codes)
        # there will be one and only one class definition
        return [n for n in mod.body if isinstance(n, ast.ClassDef)][0]
    
    def _get_mro_list(self) -> Sequence[str]:
        """Calculate the MRO list."""
        return [
            n.name for _, n in self.base_parent_info
        ]
    
    def _get_code_lens(self):
        """Get the Code Lens associated with this parsed class."""
        return {
            'range': {
                'start': {
                    # changing to line starting with 0 (LSP standard)
                    'line': self.start_pos[0] - 1,
                    'character': self.start_pos[1],
                },
                'end': {
                    # changing to line starting with 0 (LSP standard)
                    'line': self.end_pos[0] - 1,
                    'character': self.end_pos[1],
                }
            },
            'data': self.mro_list,
        }
