from typing import Dict
from jedi.api.classes import Name
from python_server.parsed_class import ParsedClass


class ParsedPackageClass(ParsedClass):

    def __init__(self, jedi_name: Name) -> None:
        super().__init__(jedi_name)
        self.mro_name_list = [self.jedi_name.name, self.OBJECT_CLASS]
        self.code_lens = self.get_code_lens()