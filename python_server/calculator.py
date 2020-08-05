import ast
import jedi
from typing import Sequence, Dict, Set, Tuple
from jedi.api import Script
from jedi.api.classes import Name


class MROCalculator:

    def __init__(
            self,
            root_uri: str,
            content_cache: Dict[str, Sequence[str]]
        ) -> None:
        self.root_uri = root_uri
        self.project = jedi.Project(path=root_uri)
        # content cache will be maintained by MROAnalyser, not in this class
        self.content_cache = content_cache
        self.jedi_scripts : Dict[str, Script] = {}
        self.parsed_names : Dict[str, Sequence[ParsedClass]] = {}
        self.outdated_scripts : Set[str] = set()
    
    def _update_script(self, script_uri: str):
        script = jedi.Script(
            code='\n'.join(self.content_cache[script_uri]),
            project=self.project,
        )
        context = script.get_context()
        self.jedi_scripts[script_uri] = script
        self.parsed_names[script_uri] = [
            ParsedClass(class_name, script)
            for class_name in script.get_names()
            if self._is_original_class(class_name, context)
        ]
    
    def mark_script_outdated(self, outdated_uri: str):
        self.outdated_scripts.add(outdated_uri)
    
    def update_all(self):
        for outdated_uri in self.outdated_scripts:
            self._update_script(outdated_uri)
        self.outdated_scripts.clear()
    
    def update_one(self, script_uri: str):
        if script_uri in self.outdated_scripts:
            self._update_script(script_uri)
            self.outdated_scripts.remove(script_uri)
    
    def get_code_lens(self, script_uri: str) -> Sequence[Dict]:
        if script_uri not in self.parsed_names:
            return []
        return [
            parsed.code_lens for parsed in self.parsed_names[script_uri]
        ]
    
    def get_code_lens_and_range(self, script_uri: str):
        if script_uri not in self.parsed_names:
            return []
        return [
            (
                parsed.code_lens,
                (
                    # changing to lines starting with 0
                    (parsed.start_pos[0] - 1, parsed.start_pos[1],),
                    (parsed.end_pos[0] - 1, parsed.end_pos[1],),
                )
            )
            for parsed in self.parsed_names[script_uri]
        ]
    
    @staticmethod
    def _is_original_class(class_name: Name, script_context: Name) -> bool:
        """
        To check if a jedi Name is an originally defined class in a script.

        Args:
            class_name: the Name of the target class
            script_context: the context of the target script
        
        Returns:
            `True` if the class is an originally defined class or `False`
            otherwise
        """
        if not script_context.full_name:
            return class_name.type == 'class'
        return class_name.type == 'class' and class_name.full_name.startswith(
            script_context.full_name)

class ParsedClass:

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
        codes = '\n'.join(self.lines)
        mod = ast.parse(codes)
        # there will be one and only one class definition
        return [n for n in mod.body if isinstance(n, ast.ClassDef)][0]
    
    def _get_mro_list(self) -> Sequence[str]:
        return [
            n.name for _, n in self.base_parent_info
        ]
    
    def _get_code_lens(self):
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
