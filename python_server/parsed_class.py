from __future__ import annotations
import ast
import jedi
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Sequence, Dict
from jedi.api import Script
from jedi.api.classes import Name


class ParsedClass(ABC):
    """
    This class encapsulates a class definition parsed for MRO list calculation
    and all the intermediate results during the calculation.

    All the necessary calculation to get the MRO list will be done during the
    initialisation of the instance.
    """

    OBJECT_CLASS : Name = jedi.Script(code='object').infer(1, 0)[0]

    def __init__(self) -> None:
        self.full_name : str = ''
        self.start_pos : Tuple[int, int] = (0, 0)
        self.end_pos : Tuple[int, int] = (0, 0)
        self.mro_list : Sequence[str] = []
        self.code_lens : Dict = {}
    
    def get_code_lens(self):
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

    @staticmethod
    def parse_by_jedi_name(
        jedi_name: Name, jedi_scripts: Dict[str, Script]
    ) -> ParsedClass:
        if not jedi_name.module_path:
            # TODO: to correct
            return ParsedPackageClass(jedi_name)
        script_path = jedi_name.module_path
        if script_path in jedi_scripts:
            return ParsedCustomClass(jedi_name, jedi_scripts[script_path])
        else:
            # TODO: may need to update the content cache
            return ParsedPackageClass(jedi_name)


from python_server.parsed_package_class import ParsedPackageClass
from python_server.parsed_custom_class import ParsedCustomClass
