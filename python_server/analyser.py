import ast
from attr.validators import instance_of
import jedi
from typing import Dict, Sequence, Tuple, Optional
from jedi.api.classes import Name


class MROAnalyser:
    """
    The actual analyser of the Python MRO Language Server. This analyser is
    responsible to manage the content of the target Python project, including
    both the persisted and unsaved contents, and to provide the analysis results
    for the MRO queries like the Hover requests and the CodeLens requests.

    All the line numbers and character/column numbers are 0-based according to
    the Language Server Protocol. Therefore, all the line numbers are
    immediately minused by one to change from 1-based (Jedi standard) to 0-based
    (LSP standard).
    """
    def __init__(self, root_uri: str) -> None:
        # the root path of the Python project directory
        self.root_dir = root_uri
        self.project = jedi.Project(path=root_uri)
        # cache the actual codes as jedi.Script does not expose the codes
        # this cache is very useful as there will be unsaved changes
        self.content_cache: Dict[str, Sequence[str]] = {}
        # cache the jedi Names of the found code lens which will be updated
        # every time the script is updated
        self.lens_names: Dict[str, Sequence[Name]] = {}
        # TODO: to refactor/improve from O(n^2) to O(n)
        # TODO: try to remove Jedi and only rely on ast
        self.class_defs: Dict[str, Sequence[ast.ClassDef]] = {}

    def replace_script_content(self, script_uri: str, content: str) -> None:
        """
        To replace the cached content of a script by the new content.

        Args:
            script_uri: the URI of the target script
            content: the new content
        """
        lines = content.splitlines()
        # to add an empty line at the end if necessary as splitlines() will not
        # add an empty line if the last character is end of line `\n`
        if not content or content[-1] == '\n':
            lines.append('')
        # update the content cache
        self.content_cache[script_uri] = lines
        # to delete the outdated found lenses, the new ones will be lazily
        # calculated when needed
        # this may lead to better performance in case of sequence of small
        # incremental changes
        if script_uri in self.lens_names:
            del self.lens_names[script_uri]

    def update_script_content(self, script_uri: str, start_pos: Tuple[int,
                                                                      int],
                              end_pos: Tuple[int, int], change: str) -> None:
        """
        To update the cached content of a script by an incremental change.

        Args:
            script_uri: the URI of the target script
            start_pos: the start position (inclusive) of the changes, in format
                of (line, character)
            end_pos: the end position (exclusive) of the changes, in format of
                (line, character)
            change: the text of the incremental changes
        """
        # fetch the lines of the old content
        lines = self.content_cache[script_uri]
        # decompose the start and end positions
        start_line, start_char = start_pos
        end_line, end_char = end_pos
        update_lines = change.splitlines()
        if not change or change[-1] == '\n':
            update_lines.append('')
        # the lines of the new content is consisted of three parts:
        new_lines = []  # placeholder for the new contents
        # 1. from the start of old content to the start position of the change
        new_lines.extend(lines[:start_line])
        new_lines.append(lines[start_line][:start_char])
        # 2. the change
        new_lines[-1] += (update_lines[0] if update_lines else '')
        new_lines.extend(update_lines[1:])
        # 3. from the end of the change to the end of the old content
        new_lines[-1] += lines[end_line][end_char:]
        new_lines.extend(lines[end_line + 1:])
        # update the content cache
        self.content_cache[script_uri] = new_lines
        # to delete the outdated found lenses, the new ones will be lazily
        # calculated when needed
        if script_uri in self.lens_names:
            del self.lens_names[script_uri]

    def update_code_lens_names_if_needed(self, script_uri: str) -> None:
        """
        To update the names of the MRO code lenses in the given script if the
        code lenses are not calculated with the updated content yet.

        Args:
            script_uri: the URI of the target script
        """
        if script_uri in self.lens_names:
            # case of already updated
            return
        if script_uri not in self.content_cache:
            # either the script is closed in the editor or something wrong
            return
        content = '\n'.join(self.content_cache[script_uri])
        script = jedi.Script(code=content)
        script_context: Name = script.get_context()
        self.lens_names[script_uri] = [
            n for n in script.get_names()
            if self._is_original_class(n, script_context)
        ]
        parsed_mod = ast.parse(content)
        self.class_defs[script_uri] = [
            child for child in parsed_mod.body
            if isinstance(child, ast.ClassDef)
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
        if script_context.full_name:
            return class_name.type == 'class' and class_name.full_name.startswith(
                script_context.full_name)
        return False

    def update_fetch_code_lens(self, script_uri: str) -> Sequence[Dict]:
        """
        To update and fetch all MRO code lenses in the target script.

        Args:
            script_uri: the URI of the target script
        
        Returns:
            the list of the found MRO code lenses
        """
        self.update_code_lens_names_if_needed(script_uri)
        return [
            self.get_code_lens_from_name(
                n,
                self.get_class_def_from_name(script_uri, n),
            )
            for n in self.lens_names[script_uri]
        ]

    def update_fetch_hover(self, script_uri: str,
                           position: Tuple[int, int]) -> Optional[Dict]:
        """
        To update and fetch the hover information for a given position of a
        given script.

        Args:
            script_uri: the URI of the target script
            position: the position of the cursor to request hover information,
                in format (line, character)
        
        Returns:
            the hover information conforming to the Language Server Protocol
            Hover Request
        """
        self.update_code_lens_names_if_needed(script_uri)
        # only need to provide hover information for the declaration positions
        # of the originally defined classes
        for lens_name in self.lens_names[script_uri]:
            if self.is_position_a_declaration(
                    position,
                    lens_name,
            ):
                return {
                    'contents': self.get_code_lens_from_name(
                        lens_name,
                        self.get_class_def_from_name(script_uri, lens_name),
                    )['data']
                }
    
    def get_class_def_from_name(self, script_uri: str, name: Name) -> Optional[ast.ClassDef]:
        for cd in self.class_defs[script_uri]:
            if cd.name == name.name:
                return cd
        return None

    @staticmethod
    def get_code_lens_from_name(name: Name, cls_def: Optional[ast.ClassDef]) -> Dict:
        """
        To get the MRO code lens from the given jedi Name.

        Args:
            the jedi Name of the target code lens
        
        Returns:
            the correspondent MRO code lens conforming to the Language Server
            Protocol Code Lens Request
        """
        def_start, def_end = MROAnalyser.get_declaration_range_from_name(name)
        return {
            'range': {
                'start': {
                    'line': def_start[0],
                    'character': def_start[1],
                },
                'end': {
                    'line': def_end[0],
                    'character': def_end[1],
                }
            },
            # 'data': MROAnalyser._DUMMY_MRO_INFO,
            'data': MROAnalyser.fetch_base_parents_from_class_def(cls_def) if cls_def else 'Unable to analyse',
        }

    # TODO: to replace this with actual MRO list calculation implementation
    _DUMMY_MRO_INFO = [
        'Target class name',
        'Parent class 1',
        'Parent class 2',
        '...',
        'Object',
    ]
    """The dummy MRO information"""

    @staticmethod
    def get_declaration_range_from_name(
            name: Name) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        To get the declaration range of the target jedi Name.

        Args:
            name: the target jedi Name
        
        Returns:
            the declaration range in format ((start_line, start_char),
            (end_line, end_char)), where start is inclusive but end is exclusive
        """
        if not name.line or not name.column:
            raise ValueError('Cannot fetch line or column from Jedi Name')
        line, col = name.line, name.column
        # line number is changed from 1-based to 0-based
        def_start = (name.line - 1, name.column)
        def_lines = name.name.split()
        if len(def_lines) == 1:
            # line number is changed from 1-based to 0-based
            def_end = (name.line - 1, name.column + len(def_lines[0]))
        else:
            # line number is changed from 1-based to 0-based
            def_end = (name.line + len(def_lines) - 1 - 1, len(def_lines[-1]))
        return def_start, def_end

    @staticmethod
    def is_position_a_declaration(position: Tuple[int, int],
                                  name: Name) -> bool:
        """
        To check if the given position is in the declaration range of the given
        jedi Name.

        Args:
            position: the position to check
            name: the target jedi Name
        
        Returns:
            `True` if the position is in the declaration range or `False`
            otherwise
        """
        def_start, def_end = MROAnalyser.get_declaration_range_from_name(name)
        return def_start <= position < def_end
    
    @staticmethod
    def fetch_base_parents_from_class_def(cls_def: ast.ClassDef) -> Sequence[str]:
        return [
            b.id if isinstance(b, ast.Name) else (
                b.value.id if isinstance(
                    b, ast.Subscript
                ) and isinstance(
                    b.value, ast.Name
                ) else 'Unknown'
            )
            for b in cls_def.bases
        ]
