import os
import sys
from collections import defaultdict

from fabric.api import local, task, runs_once


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(ROOT_DIR, 'requirements.txt')
SOURCE_DIR = os.path.join(ROOT_DIR, 'src')


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
def test():
    setup(quiet=True)
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


@task
@runs_once
def validate_config_paths(config_path=None):
    sys.path.insert(0, SOURCE_DIR)

    import yaml

    from cli import DEFAULT_CONFIG_YAML_FILEPATH

    if not config_path:
        config_path = DEFAULT_CONFIG_YAML_FILEPATH

    with open(config_path) as f:
        config = yaml.load(f.read())

    platforms = defaultdict(dict)
    platform_keys = ('cygwin', 'windows', 'osx')
    for game in config['games']:
        for platform in platform_keys:
            if platform in game:
                game_path = game[platform]['local']
                if game_path in platforms[platform]:
                    raise Exception('{} has the same source directory as another game'.format(game['name']))
                platforms[platform][game_path] = True
