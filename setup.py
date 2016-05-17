from setuptools import setup, find_packages

setup(
    name='egor',
    packages=find_packages(),
    install_requires=[
        'nameko',
    ],
    tests_require=[
        'tox',
        'pytest',
    ],
)
