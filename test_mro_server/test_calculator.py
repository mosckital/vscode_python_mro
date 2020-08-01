import pytest
import jedi
from os import path
from jedi.api.classes import Name
from typing import Sequence, Tuple
from python_server.calculator import MROCalculator


TEST_ROOT = f'{path.abspath(path.dirname(__file__))}'
ROOT_URI = path.join(TEST_ROOT, '..')
TEST_FILE_ROOT = path.join(ROOT_URI, 'tests', 'examples')
DIAMOND_FILE_PATH = path.join(TEST_FILE_ROOT, 'diamond.py')
DIAMOND_SCRIPT = jedi.Script(path=DIAMOND_FILE_PATH)
DIAMOND_CLASS_NAME_LOCATIONS = [(9, 6,), (24, 6,), (36, 6,), (48, 6,),]
DIAMOND_CLASS_NAMES : Sequence[Name] = [
	DIAMOND_SCRIPT.infer(*loc)[0] for loc in DIAMOND_CLASS_NAME_LOCATIONS
]
DIAMOND_PARENT_CLASS_STRINGS = [
	'Generic[T]', 'A', 'A', 'B, C',
]


class TestMROCalculator:
	"""Test suite for the MROCalculator class."""

	@pytest.mark.parametrize(
        ('name', 'expected',),
        list(zip(DIAMOND_CLASS_NAMES, DIAMOND_PARENT_CLASS_STRINGS))
    )
	def test_get_parent_class_str_from_class_name(
			self, name: Name, expected: str
		):
		"""Unit test for get_parent_class_str_from_class_name()."""
		assert MROCalculator.get_parent_class_str_from_class_name(name) == expected

	@pytest.mark.parametrize(
		('file_path', 'line', 'char', 'expected'),
		[
			(DIAMOND_FILE_PATH, l, c, (n, l, c + 1))
			for (l, c), n in zip(DIAMOND_CLASS_NAME_LOCATIONS, ['A', 'B', 'C', 'D'])
		]
	)
	def test_get_name_at_pos(
			self, file_path: str, line: int, char: int, expected: Tuple[str, int, int],
		):
		"""Unit test for get_name_at_pos()."""
		with open(file_path) as f:
			lines = f.readlines()
			assert MROCalculator.get_name_at_pos([""] + lines, line, char) == expected
