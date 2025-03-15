import pathlib
from setuptools import find_packages, setup


def get_version() -> str:
    rel_path = "src/loadimg/__init__.py"
    with open(rel_path, "r") as fp:
        for line in fp.read().splitlines():
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


extras = {
    "testing": [
        "setuptools",
        "wheel",
        "typing",
        "pillow",
        "numpy",
        "requests",
        "ruff",
        "pytest",
        "tqdm",
    ]
}

setup(
    name="loadimg",
    version=get_version(),
    description="a python package for loading images",
    long_description=pathlib.Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    Homepage="https://github.com/not-lain/loadimg",
    url="https://github.com/not-lain/loadimg",
    Issues="https://github.com/not-lain/loadimg/issues",
    authors=[{"name": "hafedh hichri", "email": "hhichri60@gmail.com"}],
    author_email="hhichri60@gmail.com",
    license="Apache 2.0 License",
    package_dir={"": "src"},
    packages=find_packages("src"),
    extras_require=extras,
    include_package_data=True,
    classifiers=["Topic :: Utilities", "Programming Language :: Python :: 3.9"],
    requires=["setuptools", "wheel", "typing", "pillow", "numpy", "requests", "tqdm"],
    entry_points={
        "console_scripts": [
            "loadimg=loadimg.loadimg:main",
        ],
    },
)
