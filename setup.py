import pathlib
from setuptools import setup, find_packages


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.rst").read_text()


setup(
    name='cred',
    version='0.0.0',
    packages=['cred'],
    description='Easy modeling and scenario analytics for commercial real estate debt',
    long_description=README,
    long_description_content_type='text/x-rst',
    url='https://github.com/jordanhitchcock/cred',
    author='Jordan Hitchcock',
    license='MIT',
    install_requires=['pandas>=0.25.2']
)
