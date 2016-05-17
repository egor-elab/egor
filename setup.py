from setuptools import setup, find_packages

setup(
    name='egor',
    version='0.0.0',
    url='https://github.com/egor-elab/egor/',
    packages=find_packages(),
    install_requires=[
        'nameko',
    ],
    tests_require=[
        'tox',
        'pytest',
    ],
)
