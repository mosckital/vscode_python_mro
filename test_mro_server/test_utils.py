import pytest
import yaml
import glob
from os import path
from random import randint
from typing import Callable, Generator


TEST_FILE_ROOT = path.abspath(path.dirname(__file__))
"""The root directory of the pytest files."""
EXAMPLE_FILE_ROOT = path.abspath(path.join(TEST_FILE_ROOT, '..', 'tests', 'examples'))
"""The root directory of the example python files."""
YAML_FILE_ROOT = path.abspath(path.join(TEST_FILE_ROOT, '..', 'tests', 'example_stats'))
"""The root directory of the yaml files."""


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


class TestUtils:
	"""Test suite for the test utility functions or variables."""

	@pytest.mark.parametrize(
		['file_root', 'checker'],
		[
			[
				TEST_FILE_ROOT,
				lambda f: path.isfile(f)
				and path.basename(f).startswith('test_')
				and (path.splitext(f)[1] == '.py'),
			],
			[
				EXAMPLE_FILE_ROOT,
				lambda f: path.isfile(f)
				and (path.splitext(f)[1] == '.py'),
			],
			[
				YAML_FILE_ROOT,
				lambda f: path.isfile(f)
				and (path.splitext(f)[1] in ['.yml', '.yaml']),
			],
		]
	)
	def test_file_root(self, file_root: str, checker: Callable[[str], bool]):
		"""Test if a file root is containing the correct files. """
		for file_path in glob.iglob(
				path.join(file_root, '**[!__pycache__]/*'), recursive=True
			):
			assert checker(file_path), f'{file_path} has failed check...'

	@pytest.mark.parametrize('n_exec', [1000])
	def test_gen_random_line(self, n_exec):
		"""Test if gen_random_line() can generate a line of correct max length."""
		for _ in range(n_exec):
			max_len = randint(60, 100)
			assert len(gen_random_line(max_len)) <= max_len

	@pytest.mark.parametrize(
		['file_path', 'yaml_path'],
		[
			(path.join(YAML_FILE_ROOT, 'diamond_stats.yml'), ) * 2,
		]
	)
	def test_load_yaml(self, load_yaml, file_path):
		"""Test if load_yaml() can correctly load a yaml file."""
		with open(file_path, 'r') as yaml_file:
			assert load_yaml == yaml.load(yaml_file, Loader=yaml.Loader)
