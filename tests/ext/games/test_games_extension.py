import os
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from unittest import TestCase

import yaml

from ext.games import Extension as GameBackupExtension


class TempConfig(object):
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.config_file = None

    def __enter__(self):
        self.config_file = NamedTemporaryFile(delete=False)
        yaml.dump(self.config_dict, self.config_file)
        self.config_file.close()
        return self.config_file.name

    def __exit__(self, exc_type, exc_value, traceback):
        if self.config_file:
            os.unlink(self.config_file.name)


class GamesTestCase(TestCase):
    """This has been adapted from the CLI test cases from Tasker, which worked
    very well in getting multi-process unittesting done effectively.
    https://github.com/Eagerod/tasker/blob/320fa6f334b95c8e4937d284213688073545026f/tests/test_cli.py#L24-L36
    https://github.com/Eagerod/tasker/blob/320fa6f334b95c8e4937d284213688073545026f/tests/test_cli.py#L57-L65
    """
    @classmethod
    def setUpClass(cls):
        super(GamesTestCase, cls).setUpClass()
        cls.test_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        cls.root_dir = os.path.dirname(cls.test_root_dir)

        cls.cli_path = os.path.join(cls.root_dir, 'backup', 'cli.py')

    def _call_cli(self, cli_args, stdin=None):
        full_command = ['python', self.cli_path, 'games'] + cli_args

        env = os.environ.copy()
        env['PYTHONPATH'] = self.root_dir

        process = Popen(full_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        output = process.communicate(input=stdin)
        return process.returncode, output[0], output[1]

    def test_cli_fails_without_action(self):
        rv, so, se = self._call_cli([])

        self.assertEqual(rv, 2)
        self.assertIn('too few arguments', se)

    def test_cli_fails_with_unknown_action(self):
        rv, so, se = self._call_cli(['unsave'])

        self.assertEqual(rv, 2)
        self.assertIn('invalid choice', se)

    def test_cli_fails_without_game_name(self):
        rv, so, se = self._call_cli(['save'])

        self.assertEqual(rv, 3)
        self.assertIn('No game name provided', se)

        rv, so, se = self._call_cli(['load'])

        self.assertEqual(rv, 3)
        self.assertIn('No game name provided', se)

    def test_cli_empty_config(self):
        config = {
            'manager': 'RsyncCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): '/some/root/path'
            }
        }
        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save'])
            self.assertEqual(rv, 1)
            self.assertIn('No game definitions found in {}'.format(cfg), se)

    def test_cli_no_remote(self):
        config = {
            'manager': 'RsyncCopyManager',
            'remotes': {
                'some_platform': '/lol/didnt/read'
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': '/lol/path/doesnt/matter',
                    'remote': '/somewhere/else/lol'
                }
            }]
        }
        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save'])
            self.assertEqual(rv, 1)
            self.assertIn('Cannot set up remote for this platform'.format(cfg), se)

    def test_cli_platform_empty_config(self):
        config = {
            'manager': 'RsyncCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): '/some/root/path'
            },
            'games': [{
                'name': 'Some Game',
                'some_platform': {
                    'local': '/lol/path/doesnt/matter',
                    'remote': '/somewhere/else/lol'
                }
            }]
        }
        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save'])
            self.assertEqual(rv, 1)
            self.assertIn('There are no games configured for this platform', se)

    def test_cli_unknown_copy_manager(self):
        config = {
            'manager': 'ActuallyDeletesCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): '/some/root/path'
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': '/lol/path/doesnt/matter',
                    'remote': '/somewhere/else/lol'
                }
            }]
        }
        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save'])
            self.assertEqual(rv, 1)
            self.assertIn('Failed to find copy manager: ActuallyDeletesCopyManager', se)
