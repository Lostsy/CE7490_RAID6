from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="raid6db",
    version="0.1",
    author="Shi YuMeng, Shen Yang, Tan Zhiya",
    author_email="",  # TOADD
    description="A database for storing and retrieving data",
    packages=find_packages(),
    install_requires=requirements,
)