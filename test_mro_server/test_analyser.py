import pytest
from typing import Sequence
from os import path
from random import randint
from python_server.analyser import MROAnalyser


TEST_ROOT = f'{path.abspath(path.dirname(__file__))}'
ROOT_DIR = path.abspath(path.join(TEST_ROOT, '..'))
TEST_FILE_ROOT = path.join(ROOT_DIR, 'tests', 'examples')
DIAMOND_FILE_PATH = path.join(TEST_FILE_ROOT, 'diamond.py')
DIAMOND_FILE_TEST_CASES = [
    # (line number, character number, expected success flag)
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
DIAMOND_FILE_NUM_EXPECTED_CODE_LENS = 4
DIAMOND_FILE_SUCCESS_RESULT_LOCATIONS = [
    # (line number, character number)
    # line and character are 0-based, according to Language Server Protocol
    (8, 6,),
    (23, 6,),
    (35, 6,),
    (47, 6,),
]
DIAMOND_FILE_SUCCESS_RESULT_CONTENTS = [
    ['A', 'Generic', 'object'],
    ['B', 'A', 'Generic', 'object'],
    ['C', 'A', 'Generic', 'object'],
    ['D', 'B', 'C', 'A', 'Generic', 'object'],
]
NEW_TEST_CONTENT = """

class Test:
    pass

"""
NEW_RESULT_CONTENT = ['Test', 'object']


class TestMROAnalyser:
    """Test suite for the MROAnalyser"""

    @pytest.mark.parametrize(
        ('script_path',),
        [(DIAMOND_FILE_PATH,)]
    )
    @pytest.mark.parametrize(
        ('line', 'char', 'expected',),
        DIAMOND_FILE_TEST_CASES
    )
    def test_update_fetch_hover(self, script_path: str, line: int, char: int,
                             expected: bool):
        """Test case for updating then fetching hover responses."""
        analyser = MROAnalyser(TEST_FILE_ROOT)
        with open(script_path) as script:
            analyser.replace_script_content(script_path, script.read())
            assert (analyser.update_fetch_hover(script_path, (line, char))
                    is not None) == expected
    
    @pytest.mark.parametrize(
        ('script_path',),
        [(DIAMOND_FILE_PATH,)]
    )
    @pytest.mark.parametrize(
        ('line', 'char', 'expected',),
        [
            (l, c, r) for (l, c), r in zip(
                DIAMOND_FILE_SUCCESS_RESULT_LOCATIONS,
                DIAMOND_FILE_SUCCESS_RESULT_CONTENTS
            )
        ]
    )
    def test_successful_update_fetch_hover(
            self, script_path: str, line: int, char: int, expected: Sequence[str]
        ):
        """Test case for updating, fetching and checking hover responses."""
        analyser = MROAnalyser(TEST_FILE_ROOT)
        with open(script_path) as script:
            analyser.replace_script_content(script_path, script.read())
            hover = analyser.update_fetch_hover(script_path, (line, char))
            assert hover is not None
            assert hover['contents'] == expected

    @pytest.mark.parametrize(
        (
            'script_path', 'expected_count', 'expected',
            'new_test_content', 'new_expected_result'
        ),
        [(
            DIAMOND_FILE_PATH,
            DIAMOND_FILE_NUM_EXPECTED_CODE_LENS,
            DIAMOND_FILE_SUCCESS_RESULT_CONTENTS,
            NEW_TEST_CONTENT,
            NEW_RESULT_CONTENT,
        )],
    )
    def test_successful_update_fetch_code_lens(
            self, script_path: str, expected_count: int,
            expected: Sequence[Sequence[str]],
            new_test_content: str, new_expected_result: Sequence[str]
        ):
        """Test case for updating, fetching and checking code lens responses."""
        analyser = MROAnalyser(TEST_FILE_ROOT)
        with open(script_path) as script:
            # test code lens result with the original file content
            analyser.replace_script_content(script_path, script.read())
            lenses = analyser.update_fetch_code_lens(script_path)
            assert len(lenses) == expected_count
            for lens in lenses:
                assert lens['data'] in expected
            # add new test content into the file
            lines = analyser.content_cache[script_path]
            n_last_line = len(lines) - 1
            n_last_char = len(lines[-1])
            analyser.update_script_content(
                script_path,
                (n_last_line, n_last_char),
                (n_last_line, n_last_char),
                new_test_content
            )
            # test code lens result with the new test content
            lenses = analyser.update_fetch_code_lens(script_path)
            assert len(lenses) == expected_count + 1
            for lens in lenses:
                if lens['data'] not in expected:
                    assert lens['data'] == new_expected_result
    
    @pytest.mark.parametrize(
        ('script_path', 'expected_count'),
        [(DIAMOND_FILE_PATH, DIAMOND_FILE_NUM_EXPECTED_CODE_LENS)],
    )
    def test_update_fetch_code_lens(self, script_path: str,
                                    expected_count: int):
        """Test case for updating then fetching code lens responses."""
        analyser = MROAnalyser(TEST_FILE_ROOT)
        with open(script_path) as script:
            analyser.replace_script_content(script_path, script.read())
            assert len(
                analyser.update_fetch_code_lens(script_path)
            ) == expected_count

    @staticmethod
    def gen_random_line(max_len: int) -> str:
        """
        Generate some random lines.
        
        Args:
            max_len: the max number of lines
        
        Returns:
            the generated lines
        """
        return ''.join(
            chr(randint(97, 120)) for _ in range(randint(0, max_len))
        )

    @pytest.mark.parametrize(
        ('n_times', 'max_lines', 'max_line_len'),
        [(10, 50, 80)],
    )
    def test_replace_script_content(self, n_times: int, max_lines: int,
                                    max_line_len: int):
        """Test case for the replace_script_content() method."""
        for _ in range(n_times):
            content = '\n'.join(
                TestMROAnalyser.gen_random_line(max_line_len)
                for _ in range(max_lines)
            )
            analyser = MROAnalyser('')
            file_path = 'test_file.py'
            analyser.replace_script_content(file_path, content)
            assert '\n'.join(analyser.content_cache[file_path]) == content

    @pytest.mark.parametrize(
        ('n_times', 'max_lines', 'max_line_len'),
        [(10, 50, 80)],
    )
    def test_update_script_content(self, n_times: int, max_lines: int,
                                    max_line_len: int):
        """Test case for the update_script_content() method."""
        for _ in range(n_times):
            # init analyser
            analyser = MROAnalyser('')
            file_path = 'test_file.py'
            # generate original content
            original_lines = [
                TestMROAnalyser.gen_random_line(max_line_len)
                for _ in range(max_lines)
            ]
            original_content = '\n'.join(original_lines)
            analyser.replace_script_content(file_path, original_content)
            # prepare incremental change range info
            start_line = randint(0, len(original_lines) - 1)
            end_line = randint(0, len(original_lines) - 1)
            start_char = randint(0, len(original_lines[start_line]))
            end_char = randint(0, len(original_lines[end_line]))
            if (start_line, start_char) > (end_line, end_char):
                start_line, start_char = end_line, end_char
            # prepare incremental change content
            change_lines = [
                TestMROAnalyser.gen_random_line(max_line_len)
                for _ in range(max_lines)
            ]
            change_content = '\n'.join(change_lines)
            # get invariant part before/after the change content
            prev_invariant = original_lines[:start_line + 1]
            prev_invariant[-1] = prev_invariant[-1][:start_char]
            prev_invariant = '\n'.join(prev_invariant)
            post_invariant = original_lines[end_line:]
            post_invariant[0] = post_invariant[0][end_char:]
            post_invariant = '\n'.join(post_invariant)
            # combine parts into the new content
            new_content = ''.join(
                [prev_invariant, change_content, post_invariant])
            # apply incremental update and check assertion
            analyser.update_script_content(file_path, (start_line, start_char),
                                           (end_line, end_char),
                                           change_content)
            assert '\n'.join(analyser.content_cache[file_path]) == new_content

    @pytest.mark.parametrize(
        ('script_path', 'expected_count'),
        [(DIAMOND_FILE_PATH, DIAMOND_FILE_NUM_EXPECTED_CODE_LENS)],
    )
    def test_update_code_lens_names_if_needed(self, script_path: str,
                                              expected_count: int):
        """Test if code lens can be correctely updated when needed."""
        analyser = MROAnalyser(TEST_FILE_ROOT)
        with open(script_path) as script:
            analyser.calculator.update_one(script_path)
            assert script_path not in analyser.calculator.get_code_lens(script_path)
            analyser.replace_script_content(script_path, script.read())
            assert len(
                analyser.update_fetch_code_lens(script_path)
            ) == expected_count
