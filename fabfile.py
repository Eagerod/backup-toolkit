import os
import sys
from collections import defaultdict

from fabric.api import local, task, runs_once


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILES = [
    os.path.join(ROOT_DIR, 'requirements.dev.txt'),
    os.path.join(ROOT_DIR, 'requirements.install.txt')
]
SOURCE_DIR = os.path.join(ROOT_DIR, 'src')


@task
@runs_once
def setup(quiet=False):
    for r in REQUIREMENTS_FILES:
        local('pip install {} -r {}'.format('--quiet' if quiet else '', r))


@task
@runs_once
def lint():
    setup(quiet=True)
    local('flake8 {}'.format(ROOT_DIR))


@task
@runs_once
def test(subdir=None):
    setup(quiet=True)
    if subdir:
        local('python -m unittest discover -v -t . -s tests/{}'.format(subdir))
    else:
        local('python -m unittest discover -v -t . -s tests')


@task
@runs_once
def coverage():
    setup(quiet=True)

    local('coverage erase')
    local('coverage run -m unittest discover -v -t . -s tests')
    local('coverage report -m')


@task
@runs_once
def install():
    local('pip install --upgrade -v {}'.format(ROOT_DIR))
