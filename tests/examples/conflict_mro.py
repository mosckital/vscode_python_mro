"""
This module provides examples for tests to check if the language server can
correctly deal with the case that the MRO list of the target class declaration
has conflict due to bad inheritance tree.
"""
class O: pass

class A(O): pass

class B(A): pass

class C(A, B): pass