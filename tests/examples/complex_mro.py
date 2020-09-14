"""
This module provides example for tests to check if the language server can deal
with a complex MRO list where all the relevant class declarations are in the
same module here.

The example is taken from the [Wikipedia C3 linearization page](
https://en.wikipedia.org/wiki/C3_linearization). The original author keeps the
copyright and please refer to the wiki page for more details.
"""
class O: pass

class A(O): pass

class B(O): pass

class C(O): pass

class D(O): pass

class E(O): pass

class K1(A, B, C): pass

class K2(D, B, E): pass

class K3(D, A): pass

class Z(K1, K2, K3): pass