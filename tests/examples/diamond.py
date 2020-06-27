"""The classic diamond problem for multiple inheritance.
"""
from typing import TypeVar, Generic


T = TypeVar('T')  # generic type for data


class A(Generic[T]):
    
    def func_a(self):
        pass

    def func_ab(self):
        pass

    def func_ac(self):
        pass

    def func_ad(self):
        pass


class B(A):
    
    def func_b(self):
        pass

    def func_bd(self):
        pass

    def func_ab(self):
        return super().func_ab()


class C(A):
    
    def func_c(self):
        pass

    def func_cd(self):
        pass

    def func_ac(self):
        return super().func_ac()


class D(B, C):
    
    def func_d(self):
        pass

    def func_ad(self):
        return super().func_ad()
