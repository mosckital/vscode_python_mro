"""The classic diamond problem for multiple inheritance.
"""
from typing import TypeVar, Generic


T = TypeVar('T')  # generic type for data


class A(Generic[T]):
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass
