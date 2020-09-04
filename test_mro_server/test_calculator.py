from typing import List, Tuple
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
	def prepare_analyser(script_path: str = None):
		"""Prepare a MROAnalyser populated with the content of the given script.
		"""
		analyser = MROAnalyser(EXAMPLE_FILE_ROOT)
		if script_path:
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

	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		[
			[DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
		],
	)
	def test_mark_script_outdated(self, script_path, load_yaml):
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser(script_path)
		calculator = analyser.calculator
		# the script should be already in the content cache, but not updated, so
		# acting like outdated
		assert script_path in calculator.content_cache
		self.assert_script_outdated(calculator, script_path)
		# update the script
		calculator.update_one(script_path)
		# the script should now be parsed into a Jedi Script
		assert script_path in calculator.content_cache
		self.assert_script_updated(calculator, script_path, load_yaml)
		# mark the script outdated
		calculator.mark_script_outdated(script_path)
		# the script should be outdated again
		assert script_path in calculator.content_cache
		self.assert_script_outdated(calculator, script_path)

	@pytest.mark.parametrize('n_outdated', [100])
	def test_update_all(self, n_outdated: int):
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser()
		calculator = analyser.calculator
		# inject fake script paths into outdated_scripts
		calculator.outdated_scripts.update(
			f'fake_path_{i}' for i in range(n_outdated)
		)
		assert len(calculator.outdated_scripts) == n_outdated
		# update all and check
		calculator.update_all()
		assert len(calculator.outdated_scripts) == 0
	
	@pytest.mark.parametrize('n_outdated', [100])
	def test_update_one(self, n_outdated: int):
		# the fake target script path
		target_script = 'target_script'
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser()
		calculator = analyser.calculator
		# inject fake script paths into outdated_scripts
		calculator.outdated_scripts.update(
			f'fake_path_{i}' for i in range(n_outdated)
		)
		calculator.outdated_scripts.add(target_script)
		assert len(calculator.outdated_scripts) == n_outdated + 1
		# update the target one and check
		calculator.update_one(target_script)
		assert len(calculator.outdated_scripts) == n_outdated
	
	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		[
			[DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
		],
	)
	def test_get_code_lens(self, script_path, load_yaml):
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser(script_path)
		calculator = analyser.calculator
		# update and then check the code lenses are correct
		calculator.update_all()
		lenses = calculator.get_code_lens(script_path)
		self.compare_code_lenses(lenses, load_yaml['code_lenses'])
	
	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		[
			[DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
		],
	)
	def test_get_code_lens_and_range(self, script_path, load_yaml):
		# prepare the analyser and the calculator
		analyser = self.prepare_analyser(script_path)
		calculator = analyser.calculator
		# update the script
		calculator.update_all()
		# fetch the code lenses and ranges and separate them
		fetched = calculator.get_code_lens_and_range(script_path)
		lenses = [t[0] for t in fetched]
		ranges = [t[1] for t in fetched]
		# check the code lenses are correct
		self.compare_code_lenses(lenses, load_yaml['code_lenses'])
		# check the ranges are correct
		locations = [
			(
				lens['location'][0], lens['location'][1]
			) for lens in load_yaml['code_lenses']
		]
		self.check_locations_in_ranges(ranges, locations)

	@staticmethod
	def check_locations_in_ranges(
		ranges: List[Tuple[Tuple[int, int], Tuple[int, int]]],
		locations: List[Tuple[int, int]],
	):
		# sort the ranges and locations
		ranges.sort()
		locations.sort()
		# the numbers should match
		assert len(ranges) == len(locations)
		# the location should be within the corresponding range
		for ran, loc in zip(ranges, locations):
			assert ran[0] <= loc < ran[1]
