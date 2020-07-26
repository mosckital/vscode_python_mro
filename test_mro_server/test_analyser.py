import pytest
import os.path as path
import pathlib
from python_server.analyser import MROAnalyser


TEST_ROOT = f'{path.abspath(path.dirname(__file__))}'
ROOT_URI = path.join(TEST_ROOT, '..')
TEST_FILE_ROOT = path.join(ROOT_URI, 'tests', 'examples')
DIAMOND_FILE_PATH = path.join(TEST_FILE_ROOT, 'diamond.py')
DIAMOND_FILE_TEST_CASES = [
 # (line number, character number, expected result)
 # line and character are 0-based, according to Language Server Protocol
 # all class names should be detected
 (8, 6, True,), (23, 6, True,), (35, 6, True,), (47, 6, True,),
 # keyword 'class' should not be detected
 (8, 3, False,), (23, 0, False,), (35, 5, False,), (47, 4, False,),
 # base class list should not be detected
 (8, 10, False,), (23, 8, False,), (35, 7, False,), (47, 10, False,),
 # function or other stuff should not be detected
 (2, 6, False,), (5, 0, False,), (25, 10, False,), (53, 18, False,),
]


class TestMROAnalyser:

    @pytest.mark.parametrize(
     ('script_path',),
     [(DIAMOND_FILE_PATH,)]
    )
    @pytest.mark.parametrize(
     ('line', 'char', 'expected',),
     DIAMOND_FILE_TEST_CASES
    )
    def test_is_cursor_class(self, script_path: str, line: int, char: int,
                             expected: bool):
        analyser = MROAnalyser(pathlib.Path(TEST_FILE_ROOT).as_uri())
        script_uri = pathlib.Path(script_path).as_uri()
        with open(script_path) as script:
            analyser.replace_script_content(script_uri, script.read())
            assert (analyser.fetch_hover(script_uri, (line, char))
                    is not None) == expected
