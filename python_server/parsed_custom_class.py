import ast
from python_server.parsed_package_class import ParsedPackageClass
from typing import Tuple, Sequence
from jedi.api.classes import Name
from python_server.calculator import MROCalculator
from python_server.parsed_class import ParsedClass


class ParsedCustomClass(ParsedClass):
    """
    This class encapsulates a class definition parsed for MRO list calculation
    and all the intermediate results during the calculation.

    All the necessary calculation to get the MRO list will be done during the
    initialisation of the instance.
    """

    def __init__(self, jedi_name: Name, calculator: MROCalculator) -> None:
        super().__init__(jedi_name)
        self._calculator = calculator
        module_path = jedi_name.module_path
        # the Jedi Name should have `module_path` available 
        if (not module_path):
            raise ValueError("Jedi Name's module name is not available or not registered.")
        # load the relevant script if not yet
        if module_path not in calculator.content_cache:
            with open(module_path) as loaded_module:
                calculator.replace_content_in_cache(module_path, loaded_module.read())
        # update the analysis result of the relevant script if outdated
        if module_path in calculator.outdated_scripts:
            calculator.update_one(module_path)
        # the script should now be analysed and its path can be used to search
        if module_path not in calculator.jedi_scripts_by_path:
            raise ValueError("Error when loading Jedi Name's module content into Calculator.")
        # fetch the relevant Jedi Script, get code lines and class definition
        self._jedi_script = calculator.jedi_scripts_by_path[module_path]
        self._lines = self._get_code_lines()
        self._class_def = self._get_class_def_ast_from_lines()
        # the Jedi Name should have the position information
        if self.jedi_name.line is None or self.jedi_name.column is None:
            raise ValueError(f'Parsed class {self.jedi_name.full_name} has no line or column information.')
        # positions with line starting with 1 (Jedi and AST standard)
        self.start_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column
        )
        self.end_pos : Tuple[int, int] = (
            self.jedi_name.line,
            self.jedi_name.column + len(self._class_def.name)
        )
        # calculate the Jedi Names of the base parents
        self._base_parent_names = [
            self._jedi_script.infer(
                b.lineno + self.jedi_name.line - 1,
                b.col_offset
            )[0]
            for b in self._class_def.bases
        ] if self._class_def.bases else [self.OBJECT_CLASS]
        # refine the calculated Jedi Names of the base parents to full content
        for i, base in enumerate(self._base_parent_names):
            full_candidates = base.goto()
            if full_candidates and isinstance(full_candidates[0], Name):
                self._base_parent_names[i] = full_candidates[0]
        self._mro_parsed_list = None

    @property
    def mro_parsed_list(self) -> Sequence[ParsedClass]:
        if not self._mro_parsed_list:
            self._mro_parsed_list = self._get_mro_parsed_list()
        return self._mro_parsed_list

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
        codes = '\n'.join(self._lines)
        mod = ast.parse(codes)
        # there will be one and only one class definition
        return [n for n in mod.body if isinstance(n, ast.ClassDef)][0]

    def _get_base_parent_parsed(self):
        """Get the list of base parent classes in ParseClass format."""
        return [
            self._calculator.parsed_name_by_full_name.get(
                base_name.full_name, ParsedCustomClass(base_name, self._calculator)
            ) if base_name.full_name else ParsedPackageClass(base_name)
            for base_name in self._base_parent_names
        ]

    def _get_mro_parsed_list(self) -> Sequence[ParsedClass]:
        """
        Calculate the MRO list in ParsedClass via the C3 Linearisation
        algorithm.

        Details of the algorithm can be found in the `C3 Linearisation`
        Wikipedia page.
        """
        base_parent_parsed = self._get_base_parent_parsed()
        merge_list = [base_parsed.mro_parsed_list for base_parsed in base_parent_parsed]
        merge_list.append(base_parent_parsed)
        mro_parsed_list = [self] + self._merge_mro_parsed_lists(merge_list)
        return mro_parsed_list
    
    @classmethod
    def _merge_mro_parsed_lists(cls, sublists):
        """The merge step in the C3 Linearisation algorithm to merge the MRO
        sublists (elements in ParsedClass) to one result MRO list (elements in
        ParsedClass).
        """
        if not sublists:
            return []
        # iterate over all possible next parent class (the head)
        for i, mro_list in enumerate(sublists):
            head = mro_list[0]
            good_head = True
            # check the head candidate is not in any other list tail
            for cmp_list in sublists[i + 1:]:
                for parsed in cmp_list[1:]:
                    if head == parsed:
                        good_head = False
                        break
                if not good_head:
                    break
            # construct the remaining list to merge if the head is valid
            if good_head:
                next_list = []
                for merge_item in sublists:
                    new_list = [
                        item for item in merge_item
                        if item != head
                    ]
                    if new_list:
                        next_list.append(new_list)
                return [head] + cls._merge_mro_parsed_lists(next_list)
        return []
