import pytest
from os import path
from python_server.calculator import MROCalculator
from test_mro_server.test_utils import TestUtils, EX_YAML_PAIRS, load_yaml


class TestMROCalculator:
	"""Test suite for the MROCalculator"""

	@staticmethod
	def assert_script_updated(
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
		TestUtils.compare_code_lenses(
			[name.code_lens for name in names],
			load_yaml.get('code_lenses', []),
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
		EX_YAML_PAIRS,
	)
	def test_update_script(self, script_path, load_yaml):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
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
		EX_YAML_PAIRS,
	)
	def test_mark_script_outdated(self, script_path, load_yaml):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
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
		# prepare the calculator
		calculator = TestUtils.prepare_calculator()
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
		# prepare the calculator
		calculator = TestUtils.prepare_calculator()
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
		EX_YAML_PAIRS,
	)
	def test_get_code_lens(self, script_path, load_yaml):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
		# update and then check the code lenses are correct
		calculator.update_all()
		lenses = calculator.get_code_lens(script_path)
		TestUtils.compare_code_lenses(
			lenses,
			load_yaml.get('code_lenses', []),
		)
	
	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		EX_YAML_PAIRS,
	)
	def test_get_code_lens_and_range(self, script_path, load_yaml):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
		# update the script
		calculator.update_all()
		# fetch the code lenses and ranges and separate them
		fetched = calculator.get_code_lens_and_range(script_path)
		lenses = [t[0] for t in fetched]
		ranges = [t[1] for t in fetched]
		# check the code lenses are correct
		TestUtils.compare_code_lenses(
			lenses,
			load_yaml.get('code_lenses', []),
		)
		# check the ranges are correct
		locations = [
			(
				lens['location'][0], lens['location'][1]
			) for lens in load_yaml.get('code_lenses', [])
		]
		TestUtils.assert_locations_in_ranges(ranges, locations)

	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		EX_YAML_PAIRS,
	)
	def test_is_original_class(self, script_path, load_yaml):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
		# update the script
		calculator.update_all()
		# fetch the correspondent Jedi Script and its Jedi Context
		script = calculator.jedi_scripts_by_path[script_path]
		context = script.get_context()
		# every ParsedClass should be based on an original Jedi Name
		for name in calculator.parsed_names_by_path[script_path]:
			assert calculator._is_original_class(name.jedi_name, context)
		# the number of original name should equal to the number of code lenses
		n_original = 0
		for name in script.get_names():
			if calculator._is_original_class(name, context):
				n_original += 1
		assert n_original == len(load_yaml.get('code_lenses', []))
	
	@pytest.mark.parametrize(
		'script_path',
		[
			s for s, _ in EX_YAML_PAIRS
		],
	)
	def test_parse_class_by_jedi_name(self, script_path):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
		# update the script
		calculator.update_all()
		# fetch the correspondent Jedi Script and its Jedi Context
		script = calculator.jedi_scripts_by_path[script_path]
		context = script.get_context()
		from python_server.parsed_package_class import ParsedPackageClass
		from python_server.parsed_custom_class import ParsedCustomClass
		for name in script.get_names():
			parsed_class = calculator.parse_class_by_jedi_name(name)
			if calculator._is_original_class(name, context):
				assert isinstance(parsed_class, ParsedCustomClass)
			else:
				assert isinstance(parsed_class, ParsedPackageClass)
