from jedi.api.classes import Name
from python_server.parsed_class import ParsedClass


class ParsedPackageClass(ParsedClass):

    def __init__(self, jedi_name: Name) -> None:
        super().__init__(jedi_name)
        self._mro_name_list = [self.jedi_name]
        self._mro_parsed_list = [self]
        if self.jedi_name.full_name != self.OBJECT_CLASS.full_name:
            self._mro_name_list.append(self.OBJECT_CLASS)
            self._mro_parsed_list.append(PARSED_OBJECT_CLASS)
        self._code_lens = {}

    @property
    def mro_name_list(self):
        return self._mro_name_list

    @property
    def mro_parsed_list(self):
        return self._mro_parsed_list

    @property
    def code_lens(self):
        return self._code_lens


PARSED_OBJECT_CLASS = ParsedPackageClass(ParsedPackageClass.OBJECT_CLASS)
