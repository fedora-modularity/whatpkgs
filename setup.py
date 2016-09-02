from setuptools import setup

setup(
    name='query_dnf',
    version='0.1',
    py_modules=['query_dnf'],
    install_requires=[
        'Click',
        'colorama',
        ],
    url='http://github.com/sgallagher/python3-rpm-deps',
    license='GPLv3+',
    author='Stephen Gallagher',
    author_email='sgallagh@redhat.com',
    description='Package to recursively identify RPM package dependencies',
    entry_points='''
        [console_scripts]
        query_dnf=query_dnf:main
    '''
)
