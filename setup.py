# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package contains the autorunrecord Sphinx extension.

Inspired by and based on the 'autorun' sphinx extension
by Vadim Gubergrits.
'''

requires = ['Sphinx']

setup(
    name='autorunrecord',
    version='0.2',
    url='http://github.com/mih/autorunrecord',
    license='BSD',
    author='Michael Hanke',
    author_email='michael.hanke@gmail.com',
    description='Sphinx extension autorunrecord',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
)
