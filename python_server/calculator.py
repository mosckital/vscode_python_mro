import jedi
from typing import Sequence, Dict, Set
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
            root_uri: str,
            content_cache: Dict[str, Sequence[str]]
        ) -> None:
        self.root_uri = root_uri
        self.project = jedi.Project(path=root_uri)
        # content cache will be maintained by MROAnalyser, not in this class
        self.content_cache = content_cache
        # script uri -> Jedi script
        self.jedi_scripts_by_uri : Dict[str, Script] = {}
        # script uri -> ParsedClass list of the script
        self.parsed_names_by_uri : Dict[str, Sequence[ParsedClass]] = {}
        # class full name -> ParsedClass
        self.parsed_name_by_ful_name : Dict[str, ParsedClass] = {}
        # set of the outdated scripts' uri
        self.outdated_scripts : Set[str] = set()

    def _update_script(self, script_uri: str):
        """
        To update the Jedi script and the ParsedClass list based on the given
        script uri and its cached content.

        Args:
            script_uri: the uri of the target script
        """
        if script_uri not in self.content_cache:
            return
        script = jedi.Script(
            code='\n'.join(self.content_cache[script_uri]),
            project=self.project,
        )
        context = script.get_context()
        self.jedi_scripts_by_uri[script_uri] = script
        self.parsed_names_by_uri[script_uri] = [
            ParsedClass(class_name, script)
            for class_name in script.get_names()
            # only the class defined in the script will be considered
            if self._is_original_class(class_name, context)
        ]
        for parsed in self.parsed_names_by_uri[script_uri]:
            self.parsed_name_by_ful_name[parsed.full_name] = parsed
    
    def mark_script_outdated(self, outdated_uri: str):
        """
        Mark one script as outdated, so all relevant cached intermediate results
        are no longer valid and need to be recalculated when it's requested next
        time.

        Args:
            outdated_uri: the uri of the outdated script
        """
        if outdated_uri in self.outdated_scripts:
            return
        self.outdated_scripts.add(outdated_uri)
        if outdated_uri in self.parsed_names_by_uri:
            for parsed in self.parsed_names_by_uri[outdated_uri]:
                self.parsed_name_by_ful_name.pop(
                    parsed.full_name, None
                )
        self.jedi_scripts_by_uri.pop(outdated_uri, None)
        self.parsed_names_by_uri.pop(outdated_uri, None)

    def update_all(self):
        """
        Update all the outdated scripts.
        """
        for outdated_uri in self.outdated_scripts:
            self._update_script(outdated_uri)
        self.outdated_scripts.clear()
    
    def update_one(self, script_uri: str):
        """
        Update the one specific outdated script, given its uri.

        Args:
            script_uri: the uri of the target outdated script
        """
        if script_uri in self.outdated_scripts:
            self._update_script(script_uri)
            self.outdated_scripts.remove(script_uri)
    
    def get_code_lens(self, script_uri: str) -> Sequence[Dict]:
        """
        Get the code lens list of the given script.

        Args:
            script_uri: the uri of the target script
        
        Returns:
            the list of code lens in the script
        """
        if script_uri not in self.parsed_names_by_uri:
            return []
        return [
            parsed.code_lens for parsed in self.parsed_names_by_uri[script_uri]
        ]
    
    def get_code_lens_and_range(self, script_uri: str):
        """
        Get the list of the code lens and the range of the associate parsed
        class for the given target script.

        Args:
            script_uri: the uri of the given script
        
        Returns:
            the list of the code lens and range
        """
        if script_uri not in self.parsed_names_by_uri:
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
            for parsed in self.parsed_names_by_uri[script_uri]
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
        if not script_context.full_name:
            return class_name.type == 'class'
        return class_name.type == 'class' and class_name.full_name.startswith(
            script_context.full_name)
