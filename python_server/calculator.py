import jedi
from jedi.api.classes import Name


class MROCalculator(type(Name)):

	@staticmethod
	def get_parent_class_str_from_class_name(name: Name) -> str:
		if name.type != 'class':
			raise ValueError('Should be a jedi Name for class!')
		start_pos = name.get_definition_start_position()
		end_pos = name.get_definition_end_position()
		lines = name.get_line_code(after=end_pos[0] - start_pos[0]).splitlines()
		lines[-1] = lines[-1][:end_pos[1]]
		lines[0] = lines[0][start_pos[1]:]
		sig_str = (''.join(lines)).split(':')[0]
		assert sig_str.startswith('class ')
		if '(' not in sig_str:
			return []  # no parent class, only 'object'
		return sig_str[sig_str.index('(') + 1 : len(sig_str) - 1]
