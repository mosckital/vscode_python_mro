import ast
from typing import Dict, Sequence, Tuple, Optional


class MROAnalyser:
    """
    The actual analyser of the Python MRO Language Server. This analyser is
    responsible to manage the content of the target Python project, including
    both the persisted and unsaved contents, and to provide the analysis results
    for the MRO queries like the Hover requests and the CodeLens requests.

    All the line numbers and character/column numbers are 0-based according to
    the Language Server Protocol. Therefore, all the line numbers are
    immediately minused by one to change from 1-based (Jedi standard or
    AST standard) to 0-based (LSP standard).
    """
    def __init__(self, root_uri: str) -> None:
        # the root path of the Python project directory
        self.root_dir = root_uri
        # cache the actual codes as lines
        # this cache is very useful as there will be unsaved changes
        self.content_cache: Dict[str, Sequence[str]] = {}
        # cache the found code lenses which will be updated when a relevant
        # request comes
        self.code_lenses: Dict[str, Sequence[Dict]] = {}

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
        if script_uri in self.code_lenses:
            del self.code_lenses[script_uri]

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
        if script_uri in self.code_lenses:
            del self.code_lenses[script_uri]

    def update_code_lens_names_if_needed(self, script_uri: str) -> None:
        """
        To update the names of the MRO code lenses in the given script if the
        code lenses are not calculated with the updated content yet.

        Args:
            script_uri: the URI of the target script
        """
        if script_uri in self.code_lenses:
            # case of already updated
            return
        if script_uri not in self.content_cache:
            # either the script is closed in the editor or something wrong
            return
        content = '\n'.join(self.content_cache[script_uri])
        # parse the codes and generate the abstract syntax tree
        parsed_mod = ast.parse(content)
        # update the code lens by the class definitions
        self.code_lenses[script_uri] = [
            self.get_code_lens_from_class_def(
                self.content_cache[script_uri], child
            )
            for child in parsed_mod.body
            if isinstance(child, ast.ClassDef)
        ]

    def update_fetch_code_lens(self, script_uri: str) -> Sequence[Dict]:
        """
        To update and fetch all MRO code lenses in the target script.

        Args:
            script_uri: the URI of the target script
        
        Returns:
            the list of the found MRO code lenses
        """
        self.update_code_lens_names_if_needed(script_uri)
        return self.code_lenses[script_uri]

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
        for lens in self.code_lenses[script_uri]:
            start_pos, end_pos = self.fetch_range_from_code_lens(lens)
            if start_pos <= position < end_pos:
                return {
                    'contents': lens['data'],
                }

    @staticmethod
    def fetch_base_parents_from_class_def(
            cls_def: ast.ClassDef
        ) -> Sequence[str]:
        """
        To fetch the list of base parent classes of the parsed class definition.

        Args:
            cls_def: the parsed class definition
        
        Returns:
            the list of the base parent class names
        """
        return [
            # simple case: a simple class name
            b.id if isinstance(b, ast.Name) else (
                # second simple case: a generic class
                b.value.id if isinstance(
                    b, ast.Subscript
                ) and isinstance(
                    b.value, ast.Name
                ) else 'Unknown'  # ignore the complex cases for now (very rare)
            )
            for b in cls_def.bases
        ]
    
    @staticmethod
    def get_name_range_from_class_def(
        lines: Sequence[str],
        cls_def: ast.ClassDef,
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        To get the range, both the starting line and character (inclusive) and
        the ending line and character (exclusive), of the definition name
        identifier for the given parsed class definition in the given lines of
        code.

        Args:
            lines: the lines of code
            cls_def: the target parsed class definition
        
        Returns:
            the range of the definition name identifier
        """
        # change line starting from with 1 to with 0
        # skip the starting 'class' in a class definition
        start_line, start_col = cls_def.lineno - 1, cls_def.col_offset + 5
        assert lines[start_line][start_col - 5 : start_col] == 'class', \
            f'A class definition should start with "class"'
        # rare situation: skip any non identifier character or any newline,
        # comment, line wrap etc
        # brackets are should not be allowed here so not considered
        while start_line < len(lines) and start_col < len(lines[start_line]):
            char = lines[start_line][start_col]
            if char.isalnum() or char == '_':
                # termination situation
                break
            if char in ['#', '\n', '\\']:
                # deal with advancing to new line situation
                start_line, start_col = start_line + 1, 0
            else:
                # should only be space characters like ' ' or '\t'
                start_col += 1
        # the class name is an identifier so should be in one line
        end_col = start_col + len(cls_def.name)
        return (start_line, start_col), (start_line, end_col)

    @classmethod
    def get_code_lens_from_class_def(
            cls, lines: Sequence[str], cls_def: ast.ClassDef
        ) -> Dict:
        """
        To get the MRO code lens from the code lines and the class definition.

        Args:
            lines: the lines of code
            cls_def: the parsed class definition
        
        Returns:
            the correspondent MRO code lens conforming to the Language Server
            Protocol Code Lens Request
        """
        def_start, def_end = cls.get_name_range_from_class_def(lines, cls_def)
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
            'data': cls.fetch_base_parents_from_class_def(cls_def),
        }
    
    @staticmethod
    def fetch_range_from_code_lens(
        lens: Dict
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        To fetch the range, both the starting line and character (inclusive) and
        the ending line and character (exclusive), of the definition name
        identifier for the given MRO code lens.

        Args:
            lens: the target MRO code lens:
        
        Returns:
            the range of the definition name identifier
        """
        return (
            lens['range']['start']['line'],
            lens['range']['start']['character'],
        ), (
            lens['range']['end']['line'],
            lens['range']['end']['character'],
        )
