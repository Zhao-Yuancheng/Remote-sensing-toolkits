# python setup.py build_ext --inplace

import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(
        "palette_processor_cy.pyx",
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'nonecheck': False
        }
    ),
    include_dirs=[np.get_include()]
)
