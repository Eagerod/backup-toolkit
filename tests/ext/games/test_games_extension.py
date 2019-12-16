import os
import shutil
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile, mkdtemp
from unittest import TestCase

import yaml

from backup.ext.games import Extension as GameBackupExtension


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


class SetEnv(object):
    def __init__(self, replace_envs):
        self.replace_envs = replace_envs
        self.original_envs = {}

    def __enter__(self):
        for k, v in self.replace_envs.iteritems():
            if k in os.environ:
                self.original_envs[k] = os.environ[k]
            os.environ[k] = v

    def __exit__(self, exc_type, exc_value, traceback):
        for k, v in self.replace_envs.iteritems():
            if k in self.original_envs:
                os.environ[k] = v
            else:
                del os.environ[k]


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
            'manager': 'NativeCopyManager',
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
            'manager': 'NativeCopyManager',
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
            'manager': 'NativeCopyManager',
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

    def test_cli_saves_successfully(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()
        shutil.rmtree(dest_dir)

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): dest_dir
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': source_dir
                }
            }]
        }

        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save', '--game', 'Some Game'])
            self.assertEqual(rv, 0)

        with open(os.path.join(dest_dir, os.path.basename(source_file.name))) as f:
            self.assertEqual(f.read(), expected_content)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

    def test_cli_resolves_variables(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()
        shutil.rmtree(dest_dir)

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): dest_dir
            },
            'variables': {
                'EXAMPLE_VARIABLE': 'some_dirname'
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': source_dir,
                    'remote': os.path.join('$REMOTE_ROOT', '$EXAMPLE_VARIABLE')
                }
            }]
        }

        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save', '--game', 'Some Game'])
            self.assertEqual(rv, 0)

        with open(os.path.join(dest_dir, 'some_dirname', os.path.basename(source_file.name))) as f:
            self.assertEqual(f.read(), expected_content)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

    def test_cli_resolves_variables_from_environment_first(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()
        shutil.rmtree(dest_dir)

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): dest_dir
            },
            'variables': {
                'EXAMPLE_VARIABLE': 'some_dirname'
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': source_dir,
                    'remote': os.path.join('$REMOTE_ROOT', '$EXAMPLE_VARIABLE')
                }
            }]
        }

        with TempConfig(config) as cfg, SetEnv({'EXAMPLE_VARIABLE': '123'}):
            rv, so, se = self._call_cli(['-c', cfg, 'save', '--game', 'Some Game'])
            self.assertEqual(rv, 0)

        with open(os.path.join(dest_dir, '123', os.path.basename(source_file.name))) as f:
            self.assertEqual(f.read(), expected_content)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

    def test_cli_save_fails_file_exists(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): dest_dir
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': source_dir
                }
            }]
        }

        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save', '--game', 'Some Game'])
            self.assertEqual(rv, 5)
            self.assertIn('Cannot backup save games because:', se)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

    def test_cli_saves_all_successfully(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()
        shutil.rmtree(dest_dir)

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): dest_dir
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': source_dir
                }
            }, {
                'name': 'Some Other Game',
                'some_platform': {
                    'local': '/lol/path/doesnt/matter',
                    'remote': '/somewhere/else/lol'
                }
            }]
        }

        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'save', '--all'])
            self.assertEqual(rv, 0)

        with open(os.path.join(dest_dir, os.path.basename(source_file.name))) as f:
            self.assertEqual(f.read(), expected_content)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

    def test_cli_loads_successfully(self):
        # Create some temporary files and directories that simulate save files.
        expected_content = 'This is example content for comparison.\n'

        source_dir = mkdtemp()
        dest_dir = mkdtemp()
        shutil.rmtree(dest_dir)

        source_file = NamedTemporaryFile(dir=source_dir, delete=False)
        source_file.write(expected_content)
        source_file.close()

        config = {
            'manager': 'NativeCopyManager',
            'remotes': {
                GameBackupExtension.get_system_platform(): source_dir
            },
            'games': [{
                'name': 'Some Game',
                GameBackupExtension.get_system_platform(): {
                    'local': dest_dir
                }
            }]
        }

        with TempConfig(config) as cfg:
            rv, so, se = self._call_cli(['-c', cfg, 'load', '--game', 'Some Game'])
            self.assertEqual(rv, 0)

        with open(os.path.join(dest_dir, os.path.basename(source_file.name))) as f:
            self.assertEqual(f.read(), expected_content)

        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)
