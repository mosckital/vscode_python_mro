from __future__ import annotations
from python_server.calculator import MROCalculator
import pytest
import yaml
import glob
from os import path
from random import randint
from typing import Callable, Generator, Sequence, Tuple, List
from python_server.analyser import MROAnalyser


class TestUtils:
	"""This class encapsulates the common utility functions for testing."""

	TEST_FILE_ROOT = path.abspath(path.dirname(__file__))
	"""The root directory of the pytest files."""
	TEST_FILE_ROOT_CHECKER = lambda f: path.isfile(f) \
				and path.basename(f).startswith('test_') \
				and (path.splitext(f)[1] == '.py')
	"""The checker to test if a file is a test file."""

	EXAMPLE_FILE_ROOT = path.abspath(path.join(TEST_FILE_ROOT, '..', 'tests', 'examples'))
	"""The root directory of the example python files."""
	EXAMPLE_FILE_ROOT_CHECKER = lambda f: path.isfile(f) \
				and (path.splitext(f)[1] == '.py')
	"""The checker to test if a file is an example file."""

	YAML_FILE_ROOT = path.abspath(path.join(TEST_FILE_ROOT, '..', 'tests', 'example_stats'))
	"""The root directory of the yaml files."""
	YAML_FILE_ROOT_CHECKER = lambda f: path.isfile(f) \
				and (path.splitext(f)[1] in ['.yml', '.yaml'])
	"""The checker to test if a file is a yaml file."""

	@staticmethod
	def get_target_files(dir: str, ext: str = None):
		"""
		Get the target files in a directory recursively by ignoring the
		unimportant files.

		Args:
			dir: the root directory to search
			ext: the specific extension to search
		
		Returns:
			A set of the target files.
		"""
		if not ext:
			ext = ''
		candidates = set(
			glob.iglob(
				path.join(dir, '**/[!_]*' + ext), recursive=True
			)
		) - set(
			glob.iglob(
				path.join(dir, '**/__pycache__/*'), recursive=True
			)
		)
		return [c for c in candidates if path.isfile(c)]

	@classmethod
	def get_example_stats_pairs(
		cls, ex_dir: str, stats_dir: str
	) -> Sequence[Tuple[str, str]]:
		"""
		Get a list of pairs of example file and its corresponding stats YAML
		file, based on the given root directories and in a recursive manner.

		Args:
			ex_dir: the root directory for the example files
			stats_dir: the root directory for the statistics YAML file
		
		Returns:
			A list of found pairs of example files and stats files
		"""
		ret = []
		for ex_path in cls.get_target_files(ex_dir):
			# check if it's an example file
			if cls.EXAMPLE_FILE_ROOT_CHECKER(ex_path):
				no_ext_path = path.splitext(ex_path)[0]
				stats_path = no_ext_path.replace(ex_dir, stats_dir) + '.yaml'
				# check if the corresponding stats file exists
				if path.exists(stats_path) and path.isfile(stats_path) and \
					cls.YAML_FILE_ROOT_CHECKER(stats_path):
					ret.append((ex_path, stats_path))
		return ret

	@staticmethod
	def gen_random_line(min_len: int, max_len: int = 0) -> str:
		"""
		Generate some random lines.
		
		Args:
			min_len: the min number of lines if max_len is not 0, otherwise the max
			number of the lines
			max_len: the max number of lines if not 0
		
		Returns:
			the generated lines
		"""
		if not max_len:
			min_len, max_len = 0, min_len
		return ''.join(
			chr(randint(97, 120)) for _ in range(randint(min_len, max_len))
		)
	
	@staticmethod
	def prepare_analyser(script_path: str = None) -> MROAnalyser:
		"""Prepare a MROAnalyser populated with the content of the given script.

		Args:
			script_path: the path of the script to load by the analyser at start
		
		Returns:
			the prepared MROAnalyser
		"""
		analyser = MROAnalyser(TestUtils.EXAMPLE_FILE_ROOT)
		if script_path:
			analyser.replace_script_content(script_path, open(script_path).read())
		return analyser

	@classmethod
	def prepare_calculator(cls, script_path: str = None) -> MROCalculator:
		"""
		Prepare a MROCalculator populated with the content of the given script.

		Args:
			script_path: the path of the script to load by the analyser at start
		
		Returns:
			the prepared MROCalculator
		"""
		return cls.prepare_analyser(script_path).calculator
	
	@staticmethod
	def compare_code_lenses(actual_lenses, expected_lenses):
		"""
		Compare if the actual code lenses equal to the expected code lenses.
		"""
		assert len(actual_lenses) == len(expected_lenses)
		for actual_lens in actual_lenses:
			found = False
			for expected_lens in expected_lenses:
				if expected_lens['mro'] == actual_lens['data']:
					found = True
			assert found

	@staticmethod
	def assert_locations_in_ranges(
		ranges: List[Tuple[Tuple[int, int], Tuple[int, int]]],
		locations: List[Tuple[int, int]],
	):
		"""
		Check the locations are in the correspondent range.

		The number of locations should equal to the number of ranges.

		Args:
			ranges: the list of ranges corresponding to the locations
			locations: the list of locations to check
		"""
		# sort the ranges and locations
		ranges.sort()
		locations.sort()
		# the numbers should match
		assert len(ranges) == len(locations)
		# the location should be within the corresponding range
		for ran, loc in zip(ranges, locations):
			assert ran[0] <= loc < ran[1]


EX_YAML_PAIRS = TestUtils.get_example_stats_pairs(
	TestUtils.EXAMPLE_FILE_ROOT, TestUtils.YAML_FILE_ROOT
)
"""The list of all the pairs for example file and its stats yaml file."""


@pytest.fixture
def load_yaml(yaml_path: str) -> Generator[dict, None, None]:
	"""The test fixture to load a yaml file.

	Args:
		yaml_path: the path to the yaml file

	Returns:
		the loaded yaml file in a dictionary
	"""
	with open(yaml_path, 'r') as yaml_file:
		yield yaml.load(yaml_file, Loader=yaml.Loader)


class TestTestUtils:
	"""Test suite for the test utility functions or variables."""

	@pytest.mark.parametrize(
		['ex_dir', 'stats_dir'],
		[
			(TestUtils.EXAMPLE_FILE_ROOT, TestUtils.YAML_FILE_ROOT),
		]
	)
	def test_get_example_stats_pairs(self, ex_dir: str, stats_dir: str):
		"""Test if get_example_stats_pairs() can generate correct pair list."""
		pairs = TestUtils.get_example_stats_pairs(ex_dir, stats_dir)
		ex_paths = TestUtils.get_target_files(ex_dir)
		stats_paths = TestUtils.get_target_files(stats_dir)
		assert len(pairs) == len(ex_paths) == len(stats_paths)

	@pytest.mark.parametrize(
		['file_root', 'checker'],
		[
			[
				TestUtils.TEST_FILE_ROOT,
				TestUtils.TEST_FILE_ROOT_CHECKER,
			],
			[
				TestUtils.EXAMPLE_FILE_ROOT,
				TestUtils.EXAMPLE_FILE_ROOT_CHECKER,
			],
			[
				TestUtils.YAML_FILE_ROOT,
				TestUtils.YAML_FILE_ROOT_CHECKER,
			],
		]
	)
	def test_file_root(self, file_root: str, checker: Callable[[str], bool]):
		"""Test if a file root is containing the correct files."""
		candidate_set = TestUtils.get_target_files(file_root)
		assert len(candidate_set) > 0
		for file_path in candidate_set:
			assert checker(file_path), f'{file_path} has failed check...'

	@pytest.mark.parametrize('n_exec', [1000])
	def test_gen_random_line(self, n_exec):
		"""Test if gen_random_line() can generate a line of correct max length."""
		for _ in range(n_exec):
			max_len = randint(60, 100)
			assert len(TestUtils.gen_random_line(max_len)) <= max_len

	@pytest.mark.parametrize(
		['file_path', 'yaml_path'],
		[
			(yaml_path, yaml_path) for _, yaml_path in EX_YAML_PAIRS
		]
	)
	def test_load_yaml(self, load_yaml, file_path):
		"""Test if load_yaml() can correctly load a yaml file."""
		with open(file_path, 'r') as yaml_file:
			assert load_yaml == yaml.load(yaml_file, Loader=yaml.Loader)
