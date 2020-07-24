from logging import FATAL
import jedi


class MROAnalyser:

	def __init__(self, root_uri: str) -> None:
		self.root_dir = root_uri
		self.project = jedi.Project(path=root_uri)
		self.script_cache = dict()
		self.lenses = dict()
	
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
			script = jedi.Script(path=script_uri)
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
	
	@staticmethod
	def is_position_in_name_definition_range(position, name):
		def_start = (name.line, name.column)
		def_lines = name.name.split()
		if len(def_lines) == 1:
			def_end = (name.line, name.column + len(def_lines[0]))
		else:
			def_end = (name.line + len(def_lines) - 1, len(def_lines[-1]))
		return def_start <= position < def_end