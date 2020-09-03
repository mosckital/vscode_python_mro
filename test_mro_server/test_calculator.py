import pytest
from os import path
from python_server.analyser import MROAnalyser
from python_server.calculator import MROCalculator
from test_mro_server.test_utils import EXAMPLE_FILE_ROOT, YAML_FILE_ROOT, load_yaml


DIAMOND_FILE_PATH = path.join(EXAMPLE_FILE_ROOT, 'diamond.py')
DIAMOND_STATS_PATH = path.join(YAML_FILE_ROOT, 'diamond_stats.yml')


class TestMROCalculator:
	"""Test suite for the MROCalculator"""

	@staticmethod
	def prepare_analyser(script_path: str):
		"""Prepare a MROAnalyser populated with the content of the given script.
		"""
		analyser = MROAnalyser(EXAMPLE_FILE_ROOT)
		analyser.replace_script_content(script_path, open(script_path).read())
		return analyser
	
	@staticmethod
	def compare_code_lenses(actual_lenses, expected_lenses):
		"""Compare if the actual code lenses equal to the expected code lenses.
		"""
		assert len(actual_lenses) == len(expected_lenses)
		for actual_lens in actual_lenses:
			found = False
			for expected_lens in expected_lenses:
				if expected_lens['mro'] == actual_lens['data']:
					found = True
			assert found
	
	@classmethod
	def assert_script_updated(
		cls,
		calculator: MROCalculator,
		script_path: str,
		load_yaml: dict,
	):
		# the script should now be parsed into a Jedi Script and the content
		# should match
		assert script_path in calculator.jedi_scripts_by_path
		script = calculator.jedi_scripts_by_path[script_path]
		assert script._code.strip() == open(script_path).read().strip()
		# the class definitions in the script should also be parsed and cached
		# in the two dictionaries for lookup by script path or class full name
		assert script_path in calculator.parsed_names_by_path
		names = calculator.parsed_names_by_path[script_path]
		cls.compare_code_lenses(
			[name.code_lens for name in names],
			load_yaml['code_lenses'],
		)
		for name in names:
			assert name.full_name in calculator.parsed_name_by_full_name
			assert name == calculator.parsed_name_by_full_name[name.full_name]
	
	@staticmethod
	def assert_script_outdated(
		calculator: MROCalculator,
		script_path: str,
	):
		# the script should NOT be parsed into a Jedi Script
		assert script_path not in calculator.jedi_scripts_by_path
		# there should be NO parsed classes relating to the script
		assert script_path not in calculator.parsed_names_by_path
		abs_script_path = path.abspath(script_path)
		for name in calculator.parsed_name_by_full_name.values():
			if name.jedi_name.module_path:
				assert path.abspath(
					name.jedi_name.module_path
				) != abs_script_path

	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		[
			[DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
		],
	)
	def test_update_script(self, script_path, load_yaml):
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser(script_path)
		calculator = analyser.calculator
		# the script should be already in the content cache, but not parsed into
		# a Jedi Script
		assert script_path in calculator.content_cache
		assert script_path not in calculator.jedi_scripts_by_path
		# update the script
		calculator._update_script(script_path)
		# the script should be updated now
		self.assert_script_updated(calculator, script_path, load_yaml)
