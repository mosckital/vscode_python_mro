import pytest
import os.path as path
from python_server.analyser import MROAnalyser


TEST_ROOT = f'{path.abspath(path.dirname(__file__))}'
ROOT_URI = path.join(TEST_ROOT, '..')
TEST_FILE_ROOT = path.join(ROOT_URI, 'tests', 'examples')
DIAMOND_FILE_PATH = path.join(TEST_FILE_ROOT, 'diamond.py')
DIAMOND_FILE_TEST_CASES = [
	# (line number, character number, expected result)
	# all class names should be detected
	(9, 6, True,), (24, 6, True,), (36, 6, True,), (48, 6, True,),
	# keyword 'class' should not be detected
	(9, 3, False,), (24, 0, False,), (36, 5, False,), (48, 4, False,),
	# base class list should not be detected
	(9, 10, False,), (24, 8, False,), (36, 7, False,), (48, 10, False,),
	# function or other stuff should not be detected
	(3, 6, False,), (6, 0, False,), (26, 10, False,), (54, 18, False,),
]


class TestMROAnalyser:

	@pytest.mark.parametrize(
		('script_uri',),
		[(DIAMOND_FILE_PATH,)]
	)
	@pytest.mark.parametrize(
		('line', 'char', 'expected',),
		DIAMOND_FILE_TEST_CASES
	)
	def test_is_cursor_class(self, script_uri: str, line: int, char: int, expected: bool):
		analyser = MROAnalyser(DIAMOND_FILE_PATH)
		assert analyser.is_cursor_class(script_uri, line, char) == expected