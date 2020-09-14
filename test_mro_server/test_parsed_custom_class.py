import ast
from python_server.parsed_class import ParsedClass
import pytest
from os import path
from typing import Dict
from jedi.api import Script
from python_server.calculator import MROCalculator
from test_mro_server.test_utils import TestUtils, EX_YAML_PAIRS, load_yaml


class TestParsedCustomClass:
	"""Test suite for the ParsedCustomClass."""

	@staticmethod
	def prepare_calculator_and_script(script_path: str):
		# prepare the calculator
		calculator = TestUtils.prepare_calculator(script_path)
		# update the script in calculator
		calculator.update_all()
		# get the Jedi Script
		script = calculator.jedi_scripts_by_path[script_path]
		return calculator, script
	
	@staticmethod
	def construct_parsed_custom_class(
		calculator: MROCalculator, script: Script, expected: Dict
	):
		loc = expected['location']
		# get the Jedi Name, line index starting from 1
		class_name = script.infer(loc[0] + 1, loc[1])[0]
		# construct the ParsedCustomClass and return
		return ParsedCustomClass(class_name, calculator)

	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		EX_YAML_PAIRS,
	)
	def test_get_code_lines(self, script_path, load_yaml):
		calculator, script = self.prepare_calculator_and_script(script_path)
		# get the original lines of the script
		script_lines = calculator.content_cache[script_path]
		# check against every custom defined class
		for expected in load_yaml.get('code_lenses', []):
			parsed_class = self.construct_parsed_custom_class(
				calculator, script, expected
			)
			parsed_lines = parsed_class._get_code_lines()
			# the beginning and the end may have extract codes, so using
			# `in` instead of `==`
			assert '\n'.join(parsed_lines) in '\n'.join(
				script_lines[
					expected['location'][0] : expected['location'][0] + len(parsed_lines)
				]
			)
		
	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		EX_YAML_PAIRS,
	)
	def test_get_class_def_ast_from_lines(self, script_path, load_yaml):
		calculator, script = self.prepare_calculator_and_script(script_path)
		# check against every custom defined class
		for expected in load_yaml.get('code_lenses', []):
			parsed_class = self.construct_parsed_custom_class(
				calculator, script, expected
			)
			# check that there is one and only one class definition from the
			# code lines
			codes = '\n'.join(parsed_class._lines)
			mod = ast.parse(codes)
			assert len([n for n in mod.body if isinstance(n, ast.ClassDef)]) == 1
	
	@pytest.mark.parametrize(
		['script_path', 'yaml_path'],
		EX_YAML_PAIRS,
	)
	def test_mro_parsed_list(self, script_path, load_yaml):
		calculator, script = self.prepare_calculator_and_script(script_path)
		# check against every custom defined class
		for expected in load_yaml.get('code_lenses', []):
			parsed_class = self.construct_parsed_custom_class(
				calculator, script, expected
			)
			if expected['mro'] == [ParsedClass.CONFLICT_MRO_MSG]:
				with pytest.raises(TypeError):
					parsed_mro_list = parsed_class.mro_parsed_list
			else:
				# check the parsed mro list against the expected result
				parsed_mro_list = parsed_class.mro_parsed_list
				assert [p.jedi_name.name for p in parsed_mro_list] == expected['mro']


from python_server.parsed_custom_class import ParsedCustomClass
