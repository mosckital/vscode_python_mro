from __future__ import annotations
import jedi
from abc import ABC, abstractmethod
from typing import Tuple, Sequence, Dict
from jedi.api.classes import Name


class ParsedClass(ABC):
    """
    This class encapsulates a class definition parsed for MRO list calculation
    and all the intermediate results during the calculation.

    All the necessary calculation to get the MRO list will be done during the
    initialisation of the instance.
    """

    OBJECT_CLASS : Name = jedi.Script(code='object').infer(1, 0)[0]
    """A Jedi Name to represent the `object` class."""

    def __init__(self, jedi_name: Name) -> None:
        self.jedi_name = jedi_name
        self.full_name = self.jedi_name.full_name if self.jedi_name.full_name else ''
        self.start_pos : Tuple[int, int] = (0, 0)
        self.end_pos : Tuple[int, int] = (0, 0)
        self._code_lens = None

    @property
    @abstractmethod
    def mro_parsed_list(self) -> Sequence[ParsedClass]:
        """The MRO list in ParsedClass of the target class."""
        pass

    @property
    def code_lens(self) -> Dict:
        """The code lens correspondent to this parsed class."""
        if not self._code_lens:
            self._code_lens = self.get_code_lens()
        return self._code_lens

    @property
    def mro_list(self) -> Sequence[str]:
        """The MRO list of the class."""
        return [parsed.jedi_name.name for parsed in self.mro_parsed_list]
    
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
                    'character': self.end_pos[1] - 1,
                }
            },
            'data': self.mro_list,
        }
    
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ParsedClass):
            return False
        return self.full_name == o.full_name
