import pytest
import jedi
from os import path
from jedi.api.classes import Name
from typing import Sequence
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

	@pytest.mark.parametrize(
        ('name', 'expected',),
        list(zip(DIAMOND_CLASS_NAMES, DIAMOND_PARENT_CLASS_STRINGS))
    )
	def test_get_parent_class_str_from_class_name(
		self, name: Name, expected: str
	):
		assert MROCalculator.get_parent_class_str_from_class_name(name) == expected
