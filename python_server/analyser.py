from python_server.calculator import MROCalculator
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
    def __init__(self, root_dir: str) -> None:
        # the root path of the Python project directory
        self.root_dir = root_dir
        # the MRO calculator responsible for all MRO relevant calculations
        self.calculator = MROCalculator(self.root_dir)

    def replace_script_content(self, script_path: str, content: str) -> None:
        """
        To replace the cached content of a script by the new content.

        Args:
            script_path: the path of the target script
            content: the new content
        """
        self.calculator.replace_content_in_cache(script_path, content)

    def update_script_content(self, script_path: str, start_pos: Tuple[int,
                                                                      int],
                              end_pos: Tuple[int, int], change: str) -> None:
        """
        To update the cached content of a script by an incremental change.

        Args:
            script_path: the path of the target script
            start_pos: the start position (inclusive) of the changes, in format
                of (line, character)
            end_pos: the end position (exclusive) of the changes, in format of
                (line, character)
            change: the text of the incremental changes
        """
        self.calculator.update_content_in_cache(script_path, start_pos, end_pos, change)

    def update_fetch_code_lens(self, script_path: str) -> Sequence[Dict]:
        """
        To update and fetch all MRO code lenses in the target script.

        Args:
            script_path: the path of the target script
        
        Returns:
            the list of the found MRO code lenses
        """
        self.calculator.update_one(script_path)
        return self.calculator.get_code_lens(script_path)

    def update_fetch_hover(self, script_path: str,
                           position: Tuple[int, int]) -> Optional[Dict]:
        """
        To update and fetch the hover information for a given position of a
        given script.

        Args:
            script_path: the path of the target script
            position: the position of the cursor to request hover information,
                in format (line, character)
        
        Returns:
            the hover information conforming to the Language Server Protocol
            Hover Request
        """
        self.calculator.update_one(script_path)
        for lens, (start_pos, end_pos) in \
            self.calculator.get_code_lens_and_range(script_path):
            if start_pos <= position < end_pos:
                return {
                    'contents': lens['data'],
                }
