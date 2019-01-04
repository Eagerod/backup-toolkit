import os
import stat

from fabric.api import local, task, runs_once


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

GIT_DIRECTORY = os.path.join(ROOT_DIR, '.git')
GIT_HOOKS_DIRECTORY = os.path.join(GIT_DIRECTORY, 'hooks')
REQUIREMENTS_FILE = os.path.join(ROOT_DIR, 'requirements.txt')


@task
@runs_once
def setup_hooks():
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
def setup(quiet=False):
    setup_hooks()
    local('pip install {} -r {}'.format('--quiet' if quiet else '', REQUIREMENTS_FILE))


@task
@runs_once
def lint():
    setup(quiet=True)
    local('flake8 {}'.format(ROOT_DIR))


@task
@runs_once
def install():
    local('pip install --upgrade -v {}'.format(ROOT_DIR))
