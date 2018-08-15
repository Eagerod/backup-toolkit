import os
import setuptools
import subprocess
from setuptools.command.build_py import build_py


PRIMARY_PACKAGE_EXECUTABLE_NAME = 'photos'

DEPENDENCIES = [
    'google-oauth2l==0.9.0',
    'oauth2client==2.1.0'
]


setuptools.setup(
    name=PRIMARY_PACKAGE_EXECUTABLE_NAME,
    license='MIT',
    version='0.0.1',
    description='copy content from Google Photos to a locally accessible path',
    author='Aleem Haji',
    author_email='hajial@gmail.com',
    packages=[PRIMARY_PACKAGE_EXECUTABLE_NAME],
    package_dir={PRIMARY_PACKAGE_EXECUTABLE_NAME: 'src'},
    entry_points={
        'console_scripts': [
            '{0} = {0}.backup:do_program'.format(PRIMARY_PACKAGE_EXECUTABLE_NAME)
        ]
    },
    install_requires=DEPENDENCIES
)
