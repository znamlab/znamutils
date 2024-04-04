from setuptools import setup, find_packages

setup(
    name="znamutils",
    version="v0.6",
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/znamlab/znamutils",
    license="MIT",
    author="Antonin Blot, Petr Znamenskyi",
    author_email="antonin.blot@crick.ac.uk",
    description="Common utility functions for analysis",
    install_requires=["decopatch", "makefun", "decorator"],
)
