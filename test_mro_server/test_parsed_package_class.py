import pytest
from python_server.parsed_package_class import ParsedPackageClass, PARSED_OBJECT_CLASS
from test_mro_server.test_parsed_class import MockParsedClass


class TestParsedPackageClass:
	"""Test suite for the ParsedPackageClass."""

	@pytest.mark.parametrize('n_repeat', [100])
	def test_mro_parsed_list(self, n_repeat: int):
		for _ in range(n_repeat):
			random_jedi_name = MockParsedClass.random_jedi_name()
			package_class = ParsedPackageClass(random_jedi_name)
			assert package_class.mro_parsed_list == [package_class, PARSED_OBJECT_CLASS]
		assert ParsedPackageClass(ParsedPackageClass.OBJECT_CLASS) == PARSED_OBJECT_CLASS