from distutils.core import setup

setup(
    name='PyExp',
    version='0.1.0',
    author='Aleksey Komissarov',
    author_email='ad3002@gmail.com',
    packages=['PyExp', 'PyExp.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/PyExp/',
    license='LICENSE',
    description='A microframework for small computational experiments.',
    long_description=open('README').read(),
    install_requires=[
        'pyyaml >= 3.0',
    ],
)