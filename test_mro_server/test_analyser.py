import pytest
from os import path
from random import randint
from python_server.analyser import MROAnalyser
from test_mro_server.test_utils import EXAMPLE_FILE_ROOT, YAML_FILE_ROOT, gen_random_line, load_yaml


DIAMOND_FILE_PATH = path.join(EXAMPLE_FILE_ROOT, 'diamond.py')
DIAMOND_STATS_PATH = path.join(YAML_FILE_ROOT, 'diamond_stats.yml')


class TestMROAnalyser:
    """Test suite for the MROAnalyser"""

    @staticmethod
    def prepare_analyser(script_path: str):
        """Prepare a MROAnalyser populated with the content of the given script.
        """
        analyser = MROAnalyser(EXAMPLE_FILE_ROOT)
        analyser.replace_script_content(script_path, open(script_path).read())
        return analyser

    # region hover_tests
    @pytest.mark.parametrize(
        ['script_path', 'yaml_path'],
        [
            [DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
        ],
    )
    def test_update_fetch_hover_success(self, script_path, load_yaml):
        """Test update_fetch_hover() against the successful test cases."""
        analyser = self.prepare_analyser(script_path)
        for lens in load_yaml['code_lenses']:
            location, mro = lens['location'], lens['mro']
            hover = analyser.update_fetch_hover(
                script_path, (location[0], location[1])
            )
            assert hover and hover['contents'] == mro
    
    @pytest.mark.parametrize(
        ['script_path', 'yaml_path'],
        [
            [DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
        ],
    )
    def test_update_fetch_hover_failure(self, script_path, load_yaml):
        """Test update_fetch_hover() against the failure test cases."""
        analyser = self.prepare_analyser(script_path)
        for failure in load_yaml['negative_cases']:
            location = failure['location']
            hover = analyser.update_fetch_hover(
                script_path, (location[0], location[1])
            )
            assert hover is None
    # endregion hover_tests

    # region code_lens_tests
    @pytest.mark.parametrize(
        ['script_path', 'yaml_path'],
        [
            [DIAMOND_FILE_PATH, DIAMOND_STATS_PATH],
        ],
    )
    def test_update_fetch_code_lens(self, script_path, load_yaml):
        """Test update_fetch_code_lens() against the successful test cases."""
        analyser = self.prepare_analyser(script_path)
        expected_lenses = load_yaml['code_lenses']
        # test code lens result with the original file content
        lenses = analyser.update_fetch_code_lens(script_path)
        self.compare_code_lenses(lenses, expected_lenses)
        # return if no need to test adding new content
        if 'dummy_content' not in load_yaml:
            return
        # add new test content into the file
        lines = analyser.content_cache[script_path]
        n_last_line = len(lines) - 1
        n_last_char = len(lines[-1])
        analyser.update_script_content(
            script_path,
            (n_last_line, n_last_char),
            (n_last_line, n_last_char),
            '\n'.join(load_yaml['dummy_content'])
        )
        # test code lens result with the new test content
        lenses = analyser.update_fetch_code_lens(script_path)
        expected_lenses.append(load_yaml['dummy_code_lens'])
        self.compare_code_lenses(lenses, expected_lenses)
    
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
    # endregion code_lens_tests

    # region content_update_functions
    @pytest.mark.parametrize(
        ('n_times', 'max_lines', 'max_line_len'),
        [(10, 50, 80)],
    )
    def test_replace_script_content(self, n_times: int, max_lines: int,
                                    max_line_len: int):
        """Test the correctness of the replace_script_content() method."""
        for _ in range(n_times):
            content = '\n'.join(
                gen_random_line(max_line_len)
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
        """Test the correctness of the update_script_content() method."""
        for _ in range(n_times):
            # init analyser
            analyser = MROAnalyser('')
            file_path = 'test_file.py'
            # generate original content
            original_lines = [
                gen_random_line(max_line_len)
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
                gen_random_line(max_line_len)
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
    # endregion content_update_functions
