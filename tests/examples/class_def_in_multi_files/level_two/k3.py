import sys
from os import path


CURR_EX_ROOT_DIR = path.abspath(path.join(path.dirname(__file__), '../..'))
if CURR_EX_ROOT_DIR not in sys.path:
	sys.path.insert(0, CURR_EX_ROOT_DIR)


from class_def_in_multi_files.level_one.intermediate_defs import A
from ..level_one.intermediate_defs import D


class K3(D, A): pass