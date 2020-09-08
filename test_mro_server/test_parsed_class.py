from __future__ import annotations
import keyword
import pytest
import jedi
from random import randint
from typing import Sequence
from python_server.parsed_class import ParsedClass
from test_mro_server.test_utils import TestUtils
from jedi.api.classes import Name


class MockParsedClass(ParsedClass):
	"""A mock implementation of ParsedClass for testing the latter's
	functionality."""

	def __init__(self, jedi_name: Name) -> None:
		super().__init__(jedi_name)
		# to store the Jedi Names of the MRO list
		self._mro_name_list : list[Name] = []
		# to store the ParsedClass of the MRO list
		self._mro_parsed_list : list[ParsedClass] = []
		# randomly generate the start and end positions
		self.start_pos = (randint(1, 10), randint(0, 80))
		self.end_pos = (self.start_pos[0] + randint(1, 10), randint(0, 80))

	@property
	def mro_parsed_list(self) -> Sequence[ParsedClass]:
		return self._mro_parsed_list
	
	@classmethod
	def random_mock_class(
		cls, n_mro: int = 5, max_name_len: int = 10
	) -> MockParsedClass:
		"""Randomly generate a MockParsedClass for test."""
		parsed = MockParsedClass(cls.random_jedi_name(max_name_len))
		# randomly generate the MRO list in Jedi Name
		parsed._mro_name_list = [
			cls.random_jedi_name(max_name_len) for _ in range(n_mro)
		]
		# construct the MRO list in ParsedClass from the one in Jedi Name
		parsed._mro_parsed_list = [
			MockParsedClass(n) for n in parsed._mro_name_list
		]
		return parsed

	@staticmethod
	def random_jedi_name(max_name_len: int = 10) -> Name:
		"""Randomly generate a Jedi Name for class definition."""
		class_name = TestUtils.gen_random_line(1, max_name_len)
		# regenerate the class name if the generated is a keyword
		while keyword.iskeyword(class_name):
			class_name = TestUtils.gen_random_line(1, max_name_len)
		code = f'class {class_name}: pass'
		return jedi.Script(code=code).infer(1, 6)[0]


class TestParsedClass:
	"""Test suite for the ParsedClass."""

	def test_object_class(self):
		assert ParsedClass.OBJECT_CLASS.full_name == 'builtins.object'

	@pytest.mark.parametrize('n_repeat', [100])
	def test_code_lens(self,  n_repeat: int):
		for _ in range(n_repeat):
			parsed = MockParsedClass.random_mock_class()
			# _code_lens should have not been calculated by default
			assert parsed._code_lens is None
			# calling the property to implicitly calculate the code lens
			fetched_code_lens = parsed.code_lens
			# check the correctness of the property
			assert parsed._code_lens == fetched_code_lens
	
	@pytest.mark.parametrize('n_repeat', [100])
	def test_mro_list(self, n_repeat: int):
		for _ in range(n_repeat):
			parsed = MockParsedClass.random_mock_class()
			assert parsed.mro_list == [n.name for n in parsed._mro_name_list]

	@pytest.mark.parametrize('n_repeat', [100])
	def test_get_code_lens(self, n_repeat: int):
		for _ in range(n_repeat):
			parsed = MockParsedClass.random_mock_class()
			lens = parsed.get_code_lens()
			# check the correctness of every fields
			assert lens['data'] == [n.name for n in parsed._mro_name_list]
			assert lens['range']['start']['line'] == parsed.start_pos[0] - 1
			assert lens['range']['start']['character'] == parsed.start_pos[1]
			assert lens['range']['end']['line'] == parsed.end_pos[0] - 1
			assert lens['range']['end']['character'] == parsed.end_pos[1] - 1

	@pytest.mark.parametrize('n_repeat', [100])
	def test_eq(self, n_repeat: int):
		for _ in range(n_repeat):
			# ParsedClass should not equal to non-ParsedClass
			assert MockParsedClass.random_mock_class() != 'text'
			assert MockParsedClass.random_mock_class() != 100
			# ParsedClass of same full name should equal
			common_name = MockParsedClass.random_jedi_name()
			assert MockParsedClass(common_name) == MockParsedClass(common_name)
			# ParsedClass of different full name should not equal
			other_name = MockParsedClass.random_jedi_name()
			while other_name.full_name == common_name.full_name:
				other_name = MockParsedClass.random_jedi_name()
			assert MockParsedClass(common_name) != MockParsedClass(other_name)
			# ParsedClass of same full name should equal, a second check
			random_parsed = MockParsedClass.random_mock_class()
			assert random_parsed == MockParsedClass(random_parsed.jedi_name)
