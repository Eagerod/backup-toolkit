import os
import stat

from fabric.api import local, task, runs_once


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILES = [
    os.path.join(ROOT_DIR, 'requirements.dev.txt'),
    os.path.join(ROOT_DIR, 'requirements.install.txt')
]

GIT_DIRECTORY = os.path.join(ROOT_DIR, '.git')
GIT_HOOKS_DIRECTORY = os.path.join(GIT_DIRECTORY, 'hooks')
SOURCE_DIR = os.path.join(ROOT_DIR, 'backup')


@task
@runs_once
def setup(quiet=False):
    for r in REQUIREMENTS_FILES:
        local('pip install {} -r {}'.format('--quiet' if quiet else '', r))

    pre_commit_file = os.path.join(GIT_HOOKS_DIRECTORY, 'pre-commit')
    with open(pre_commit_file, 'w') as f:
        f.write('flake8 $(git diff --name-only --cached --diff-filter=AMRTX)')
        f.write('\n')

    user_perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    group_perms = stat.S_IRGRP | stat.S_IXGRP
    other_perms = stat.S_IROTH | stat.S_IXOTH
    os.chmod(pre_commit_file, user_perms | group_perms | other_perms)


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
