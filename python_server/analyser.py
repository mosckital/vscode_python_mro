from os import stat
import jedi
from urllib.parse import unquote, urlparse


class MROAnalyser:

    def __init__(self, root_uri: str) -> None:
        self.root_dir = root_uri
        self.project = jedi.Project(path=root_uri)
        # cache the actual codes as jedi.Script does not expose the codes
        # this cache is very useful as there will be unsaved changes
        self.content_cache = dict()
        # cache the jedi.Script which will be often updated
        self.script_cache = dict()
        # cache the found code lens which will be updated every time the script
        # is updated
        self.lenses = dict()

    def replace_script_content(self, script_uri: str, content: str) -> None:
        lines = content.splitlines()
        if not content or content[-1] == '\n':
            lines.append('')
        self.content_cache[script_uri] = lines
        self.script_cache[script_uri] = jedi.Script(code=content)
        # self.update_code_lenses(script_uri)

    def update_script_content(self, script_uri: str, change: dict) -> None:
        # fetch the lines of the old content
        lines = self.content_cache[script_uri]
        # decompose the incremental change
        start = change['range']['start']
        start_line, start_char = start['line'], start['character']
        end = change['range']['end']
        end_line, end_char = end['line'], end['character']
        update_lines = self._split_lines(change['text'])
        # the lines of the new content is consisted of three parts:
        # 1. from the start of old content to the start position of the change
        # 2. the change
        # 3. from the end of the change to the end of the old content
        new_lines = []
        new_lines.extend(lines[:start_line])
        new_lines.append(lines[start_line][:start_char] + (update_lines[0] if update_lines else ''))
        new_lines.extend(update_lines[1:])
        new_lines[-1] += lines[end_line][end_char:]
        new_lines.extend(lines[end_line + 1:])
        # update in the recording dict
        self.content_cache[script_uri] = new_lines
        self.script_cache[script_uri] = '\n'.join(new_lines)
        # self.update_code_lenses(script_uri)

    def is_cursor_class(self, script_uri: str, line: int, char: int) -> bool:
        if script_uri not in self.lenses:
            self.update_code_lenses(script_uri)
        lenses = self.lenses[script_uri]
        cursor_names = self._get_script_by_uri(script_uri).infer(line, char)
        if not any(self.is_position_in_name_definition_range((line, char), name) for name in cursor_names):
            return False
        for lens in lenses:
            for name in cursor_names:
                if lens == name:
                    return True
        return False

    def _get_script_by_uri(self, script_uri: str) -> jedi.Script:
        if script_uri in self.script_cache:
            script = self.script_cache[script_uri]
        else:
            script = jedi.Script(path=self.uri_to_path(script_uri))
            self.script_cache[script_uri] = script
        return script

    def update_code_lenses(self, script_uri: str):
        script = self._get_script_by_uri(script_uri)
        self.lenses[script_uri] = [
            n for n in script.get_names()
            if n.type == 'class' and n.full_name.startswith(
                script.get_context().full_name
            )
        ]
    
    def fetch_code_lens(self, script_uri):
        self.update_code_lenses(script_uri)
        return [self.get_code_lens_from_name(n) for n in self.lenses[script_uri]]
    
    def fetch_hover(self, script_uri, position):
        for lens_name in self.lenses[script_uri]:
            if self.is_position_in_name_definition_range(
                (position['line'], position['character']),
                lens_name,
            ):
                return {
                    'contents': self.get_code_lens_from_name(lens_name)['data']
                }

    @staticmethod
    def get_code_lens_from_name(name):
        def_start, def_end = MROAnalyser.from_name_to_range(name)
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
            'data': [
                'Target class name',
                'Parent class 1',
                'Parent class 2',
                '...',
                'Object',
            ],
        }
    
    @staticmethod
    def from_name_to_range(name):
        def_start = (name.line, name.column)
        def_lines = name.name.split()
        if len(def_lines) == 1:
            def_end = (name.line, name.column + len(def_lines[0]))
        else:
            def_end = (name.line + len(def_lines) - 1, len(def_lines[-1]))
        return def_start, def_end

    @staticmethod
    def is_position_in_name_definition_range(position, name):
        def_start, def_end = MROAnalyser.from_name_to_range(name)
        return def_start <= position < def_end

    @staticmethod
    def uri_to_path(uri: str) -> str:
        return unquote(urlparse(uri).path)
