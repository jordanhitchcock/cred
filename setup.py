import pathlib
from setuptools import setup


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.rst").read_text()


setup(
    name='cred',
    version='0.0.1',
    packages=['cred'],
    description='Easy modeling and scenario analytics for commercial real estate debt',
    long_description=README,
    long_description_content_type='text/x-rst',
    url='https://github.com/jordanhitchcock/cred',
    author='Jordan Hitchcock',
    license='MIT',
    python_requires='>=3.7',
    install_requires=['pandas>=0.25.2'],
    tests_require=['pytest'],
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment',
        'Intended Audience :: Financial and Insurance Industry',
        'Development Status :: 4 - Beta'
    ]
)
