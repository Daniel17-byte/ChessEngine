from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np
import os
import sys

# ── Aggressive compiler directives for maximum speed ─────────────────────────
cython_directives = {
    "language_level": "3",
    "boundscheck": False,
    "wraparound": False,
    "cdivision": True,
    "nonecheck": False,
    "initializedcheck": False,
    "overflowcheck": False,
}

# ── Platform-specific C compiler flags ───────────────────────────────────────
extra_compile_args = ["-O3", "-ffast-math"]
if sys.platform == "darwin":
    extra_compile_args += ["-march=native", "-flto"]
elif sys.platform.startswith("linux"):
    extra_compile_args += ["-march=native", "-flto", "-funroll-loops"]

extra_link_args = []
if sys.platform == "darwin":
    extra_link_args += ["-flto"]
elif sys.platform.startswith("linux"):
    extra_link_args += ["-flto"]

include_dirs = [np.get_include()]

# ── Extension modules ────────────────────────────────────────────────────────
extensions = [
    Extension(
        name="fastgame.board_encode",
        sources=["fastgame/board_encode.pyx"],
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        name="fastgame.game_core",
        sources=["fastgame/game_core.pyx"],
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        name="fastgame.game_eval",
        sources=["fastgame/game_eval.pyx"],
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
    Extension(
        name="fastgame.fast_training_loop",
        sources=["fastgame/fast_training_loop.pyx"],
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name="ai_engine_cython",
    ext_modules=cythonize(
        extensions,
        compiler_directives=cython_directives,
        annotate=True,  # generates HTML showing Python/C interaction
    ),
)
