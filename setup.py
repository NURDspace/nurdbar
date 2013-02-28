#!/usr/bin/env python

from setuptools import setup

install_requires=[
    'sqlalchemy'
]
setup(name='Nurdbar',
      version='0.1',
      description='Nurdspace Bar Cash Register',
      author='Dolf Andringa',
      author_email='dolfandringa@gmail.comg',
      url='http://www.nurdspace.nl/NURDbar/',
      packages=[
        'nurdbar'
      ],
      install_requires=install_requires
     )
