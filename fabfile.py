import os
import sys

from fabric.api import local, task, runs_once, warn_only


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

    # To test things in the CLI, coverage has to be started with, and all subprocesses within have to be started with
    # COVERAGE_PROCESS_START (http://coverage.readthedocs.io/en/coverage-4.2/subprocess.html).
    # A sitecustomize.py file must also be created to that when python subprocesses are fired up, they can recognize
    # that they're a part of a coverage run.
    coverage_file = os.path.join(ROOT_DIR, '.coveragerc')
    sitecustomize_path = os.path.join(ROOT_DIR, 'sitecustomize.py')
    sitecustomize_pyc_path = '{}c'.format(sitecustomize_path)

    sitecustomize_file_contents = 'import coverage\ncoverage.process_startup()\n'

    with open(sitecustomize_path, 'w') as f:
        f.write(sitecustomize_file_contents)

    with warn_only():
        r1 = local('coverage erase')
        r2 = local('COVERAGE_PROCESS_START={} coverage run -m unittest discover -v -t . -s tests'.format(coverage_file))
        r3 = local('coverage combine')
        r4 = local('coverage report -m')

    os.unlink(sitecustomize_path)

    # Avoid any residual effects of having a pyc file present.
    if os.path.exists(sitecustomize_pyc_path):
        os.unlink(sitecustomize_pyc_path)

    for result in (r for r in (r1, r2, r3, r4) if r.failed):
        sys.exit(result.return_code)


@task
@runs_once
def install():
    local('pip install --upgrade -v {}'.format(ROOT_DIR))
