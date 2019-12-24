import os
from collections import defaultdict
from unittest import TestCase

import yaml

from backup import ext


CONFIG_YAML_PATH = os.path.join(ext.__path__[0], 'games', 'config.yaml')
PLATFORM_KEY_BLACKLIST = (
    'name',
    'aliases'
)


class ConfigYamlTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ConfigYamlTestCase, cls).setUpClass()

        cls.config_yaml = yaml.load(open(CONFIG_YAML_PATH).read())

    def test_is_valid(self):
        platforms = defaultdict(dict)

        for game in self.config_yaml['games']:
            for platform in game:
                if platform in PLATFORM_KEY_BLACKLIST:
                    continue

                game_path = game[platform]['local']
                if game_path in platforms[platform]:
                    raise Exception(
                        '{} for {} has the same source directory as another game'.format(game['name'], platform)
                    )
                platforms[platform][game_path] = True
