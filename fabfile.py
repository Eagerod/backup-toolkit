from fabric.api import local, task, runs_once


@task
@runs_once
def setup(quiet=False):
    local('pip install {} -r requirements.txt'.format('--quiet' if quiet else ''))


@task
@runs_once
def lint():
    setup(quiet=True)
    local('flake8 .')


@task
@runs_once
def install_globally():
    local('pip install --upgrade .')
