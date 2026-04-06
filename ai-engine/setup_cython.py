from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        name="fastgame.game_core",
        sources=["fastgame/game_core.pyx"],
        include_dirs=[np.get_include()],
    ),
    Extension(
        name="fastgame.game_eval",
        sources=["fastgame/game_eval.pyx"],
        include_dirs=[np.get_include()],
    ),
    Extension(
        name="fastgame.board_encode",
        sources=["fastgame/board_encode.pyx"],
        include_dirs=[np.get_include()],
    ),
]

setup(
    name="ai_engine_cython",
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
)
