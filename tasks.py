import os
import stat
import sys

from invoke import task


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILES = [
    os.path.join(ROOT_DIR, 'requirements.dev.txt'),
    os.path.join(ROOT_DIR, 'requirements.install.txt')
]

GIT_DIRECTORY = os.path.join(ROOT_DIR, '.git')
GIT_HOOKS_DIRECTORY = os.path.join(GIT_DIRECTORY, 'hooks')
SOURCE_DIR = os.path.join(ROOT_DIR, 'backup')


@task
def setup(c, quiet=False):
    for r in REQUIREMENTS_FILES:
        c.run('pip3 install {} -r {}'.format('--quiet' if quiet else '', r))

    pre_commit_file = os.path.join(GIT_HOOKS_DIRECTORY, 'pre-commit')
    with open(pre_commit_file, 'w') as f:
        f.write('flake8 $(git diff --name-only --cached --diff-filter=AMRTX | grep ".py$")')
        f.write('\n')

    user_perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    group_perms = stat.S_IRGRP | stat.S_IXGRP
    other_perms = stat.S_IROTH | stat.S_IXOTH
    os.chmod(pre_commit_file, user_perms | group_perms | other_perms)


@task
def lint(c):
    setup(c, quiet=True)
    c.run('flake8 {}'.format(ROOT_DIR))


@task
def test(c, subdir=None):
    setup(c, quiet=True)
    if subdir:
        c.run('python3 -m unittest discover -v -t . -s tests/{}'.format(subdir))
    else:
        c.run('python3 -m unittest discover -v -t . -s tests')


@task
def coverage(c):
    setup(c, quiet=True)

    # To test things in the CLI, coverage has to be started with, and all
    #   subprocesses within have to be started with COVERAGE_PROCESS_START.
    #   (http://coverage.readthedocs.io/en/coverage-4.2/subprocess.html).
    # A sitecustomize.py file must also be created to that when python
    #   subprocesses are fired up, they can recognize that they're a part of a
    #   coverage run.
    coverage_file = os.path.join(ROOT_DIR, '.coveragerc')
    sitecustomize_path = os.path.join(ROOT_DIR, 'sitecustomize.py')
    sitecustomize_pyc_path = '{}c'.format(sitecustomize_path)

    sitecustomize_file_contents = 'import coverage\ncoverage.process_startup()\n'

    with open(sitecustomize_path, 'w') as f:
        f.write(sitecustomize_file_contents)

    r1 = c.run('coverage erase', warn=True)
    r2 = c.run(
        'COVERAGE_PROCESS_START={} coverage run -m unittest discover -v -t . -s tests'.format(coverage_file),
        warn=True
    )
    r3 = c.run('coverage combine', warn=True)
    r4 = c.run('coverage report -m', warn=True)

    os.unlink(sitecustomize_path)

    # Avoid any residual effects of having a pyc file present.
    if os.path.exists(sitecustomize_pyc_path):
        os.unlink(sitecustomize_pyc_path)

    for result in (r for r in (r1, r2, r3, r4) if r.failed):
        sys.exit(result.return_code)


@task
def install(c):
    c.run('pip3 install --upgrade -v {}'.format(ROOT_DIR))
