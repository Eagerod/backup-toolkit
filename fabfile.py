import os

from fabric.api import local, task, runs_once


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(ROOT_DIR, 'requirements.txt')


@task
@runs_once
def setup(quiet=False):
    local('pip install {} -r {}'.format('--quiet' if quiet else '', REQUIREMENTS_FILE))


@task
@runs_once
def lint():
    setup(quiet=True)
    local('flake8 {}'.format(ROOT_DIR))


@task
@runs_once
def install_globally():
    local('pip install --upgrade {}'.format(ROOT_DIR))
