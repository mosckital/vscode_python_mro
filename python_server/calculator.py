import jedi
from typing import Sequence, Dict, Set, List, Tuple
from jedi.api import Script
from jedi.api.classes import Name
from python_server.parsed_class import ParsedClass


class MROCalculator:
    """
    This class is responsible for calculating the MRO list of a given target and
    construct the code lens or hover response based on the calculated MRO list.
    It will also cache the intermediate results of the calculation to accelerate
    the potential similar requests in the future.
    """

    def __init__(
            self,
            root_dir: str,
        ) -> None:
        self.root_dir = root_dir
        self.project = jedi.Project(path=root_dir)
        # cache the actual codes as lines
        # this cache is very useful as there will be unsaved changes
        self.content_cache: Dict[str, Sequence[str]] = {}
        # script path -> Jedi script
        self.jedi_scripts_by_path : Dict[str, Script] = {}
        # script path -> ParsedClass list of the script
        self.parsed_names_by_path : Dict[str, Sequence[ParsedClass]] = {}
        # class full name -> ParsedClass
        self.parsed_name_by_full_name : Dict[str, ParsedClass] = {}
        # set of the outdated scripts' path
        self.outdated_scripts : Set[str] = set()

    def replace_content_in_cache(self, script_path: str, content: str) -> None:
        """
        To replace the cached content of a script by the new content.

        Args:
            script_path: the path of the target script
            content: the new content
        """
        lines = content.splitlines()
        # to add an empty line at the end if necessary as splitlines() will not
        # add an empty line if the last character is end of line `\n`
        if not content or content[-1] == '\n':
            lines.append('')
        # update the content cache
        self.content_cache[script_path] = lines
        # to mark the outdated script
        # this may lead to better performance in case of sequence of small
        # incremental changes
        self.mark_script_outdated(script_path)

    def update_content_in_cache(self, script_path: str, start_pos: Tuple[int,
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
        # fetch the lines of the old content
        lines = self.content_cache[script_path]
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
        self.content_cache[script_path] = new_lines
        # to mark the outdated script
        self.mark_script_outdated(script_path)

    def _update_script(self, script_path: str):
        """
        To update the Jedi script and the ParsedClass list based on the given
        script path and its cached content.

        Args:
            script_path: the path of the target script
        """
        # remove the script out of the `outdated_scripts` to avoid infinite loop
        self.outdated_scripts.remove(script_path)
        # nothing to do if the script is not cached
        if script_path not in self.content_cache:
            return
        script = jedi.Script(
            code='\n'.join(self.content_cache[script_path]),
            path=script_path,
            project=self.project,
        )
        context = script.get_context()
        self.jedi_scripts_by_path[script_path] = script
        self.parsed_names_by_path[script_path] = [
            # ParsedClass.parse(class_name, script)
            self.parse_class_by_jedi_name(class_name)
            # ParsedClass.parse_by_jedi_name(class_name, self.jedi_scripts_by_path)
            for class_name in script.get_names()
            # only the class defined in the script will be considered
            if self._is_original_class(class_name, context)
        ]
        for parsed in self.parsed_names_by_path[script_path]:
            self.parsed_name_by_full_name[parsed.full_name] = parsed
    
    def mark_script_outdated(self, outdated_path: str):
        """
        Mark one script as outdated, so all relevant cached intermediate results
        are no longer valid and need to be recalculated when it's requested next
        time.

        Args:
            outdated_path: the path of the outdated script
        """
        if outdated_path in self.outdated_scripts:
            return
        self.outdated_scripts.add(outdated_path)
        if outdated_path in self.parsed_names_by_path:
            # delete all cached parsed classes
            for parsed in self.parsed_names_by_path[outdated_path]:
                self.parsed_name_by_full_name.pop(
                    parsed.full_name, None
                )
        # delete cached Jedi scripts and parsed classes entries
        self.jedi_scripts_by_path.pop(outdated_path, None)
        self.parsed_names_by_path.pop(outdated_path, None)

    def update_all(self):
        """
        Update all the outdated scripts.
        """
        # use a copy of the set as `self._update_script()`` will modify the set
        # in iteration
        for outdated_path in self.outdated_scripts.copy():
            self._update_script(outdated_path)
    
    def update_one(self, script_path: str):
        """
        Update the one specific outdated script, given its path.

        Args:
            script_path: the path of the target outdated script
        """
        if script_path in self.outdated_scripts:
            self._update_script(script_path)
    
    def get_code_lens(self, script_path: str) -> Sequence[Dict]:
        """
        Get the code lens list of the given script.

        Args:
            script_path: the path of the target script
        
        Returns:
            the list of code lens in the script
        """
        if script_path not in self.parsed_names_by_path:
            return []
        return [
            parsed.code_lens for parsed in self.parsed_names_by_path[script_path]
        ]
    
    def get_code_lens_and_range(
        self, script_path: str
    ) -> List[Tuple[Dict, Tuple[Tuple[int, int], Tuple[int, int]]]]:
        """
        Get the list of the code lens and the range of the associate parsed
        class for the given target script.

        Args:
            script_path: the path of the given script
        
        Returns:
            the list of the code lens and range
        """
        if script_path not in self.parsed_names_by_path:
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
            for parsed in self.parsed_names_by_path[script_path]
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
        if not script_context.module_name:
            return class_name.type == 'class'
        # use `class_name.goto()[0]` to fetch the full content Jedi Name which
        # has the `full_name` field
        return class_name.type == 'class' and \
            class_name.goto()[0].full_name.startswith(
            script_context.module_name
        )
    
    def parse_class_by_jedi_name(
        self, jedi_name: Name
    ) -> ParsedClass:
        """
        To parse a class definition by its Jedi Name.

        Args:
            jedi_name: the Jedi Name of the target class to parse
        
        Returns:
            The parsed class in ParsedClass
        """
        # case of being the object class
        if jedi_name.full_name == 'builtins.object':
            return PARSED_OBJECT_CLASS
        # case of a class not defined by a recognised script, so external class
        if not jedi_name.module_path:
            return ParsedPackageClass(jedi_name)
        # case of a custom class definition, which should have a dot-separate
        # full name starting with the full name of the module/script, and its
        # type should be `class`. There is case that the first condition is
        # satisfied but the second not, like a type alias definition/assignment
        # has a type `statement`.
        # use `class_name.goto()[0]` to fetch the full content Jedi Name which
        # has the `full_name` field
        if jedi_name.goto()[0].full_name.startswith(
            jedi_name.module_name
        ) and jedi_name.type == 'class':
            return ParsedCustomClass(jedi_name, self)
        else:
            return ParsedPackageClass(jedi_name)


from python_server.parsed_package_class import ParsedPackageClass, PARSED_OBJECT_CLASS
from python_server.parsed_custom_class import ParsedCustomClass
