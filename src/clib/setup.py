from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        'galois_field',
        ['galois_field.cpp', 'parity.cpp', 'bindings.cpp'],
        include_dirs=[pybind11.get_include()],
        extra_compile_args=['-std=c++11'],
        language='c++'
    ),
]

setup(
    name='galois_field',
    ext_modules= ext_modules,
)
