from typing import Dict
from jedi.api.classes import Name
from python_server.parsed_class import ParsedClass


class ParsedPackageClass(ParsedClass):

    def __init__(self, jedi_name: Name) -> None:
        super().__init__()
        self.jedi_name = jedi_name
        self.full_name = self.jedi_name.full_name if self.jedi_name.full_name else ''
        self.mro_list = [self.jedi_name.name, 'object']
        self.code_lens = self.get_code_lens()