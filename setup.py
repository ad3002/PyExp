import re
import os
from setuptools import setup

version = None
for line in open('./PyExp/__init__.py'):
    m = re.search('__version__\s*=\s*(.*)', line)
    if m:
        version = m.group(1).strip()[1:-1]  # quotes
        break
assert version

setup(
    name='PyExp',
    version=version,
    author='Aleksey Komissarov',
    author_email='ad3002@gmail.com',
    packages=['PyExp'],
    package_data={
        '': ['README.md']
    },
    include_package_data=True,
    scripts=[],
    url='http://github.com/ad3002/PyExp',
    license='BSD',
    description='A microframework for small computational experiments.',
    install_requires=[
        'pyyaml >= 3.0',
        'simplejson >= 1.0',
        'logbook >= 0.7',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
)