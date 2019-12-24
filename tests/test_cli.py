import os
import sys
from subprocess import Popen, PIPE

from unittest import TestCase


PYTHON_BIN = sys.argv[0].split(" ")[0]


class CliTestCase(TestCase):
    """This has been adapted from the CLI test cases from Tasker, which worked
    very well in getting multi-process unittesting done effectively.
    https://github.com/Eagerod/tasker/blob/320fa6f334b95c8e4937d284213688073545026f/tests/test_cli.py#L24-L36
    https://github.com/Eagerod/tasker/blob/320fa6f334b95c8e4937d284213688073545026f/tests/test_cli.py#L57-L65
    """
    @classmethod
    def setUpClass(cls):
        super(CliTestCase, cls).setUpClass()
        cls.test_root_dir = os.path.dirname(os.path.realpath(__file__))
        cls.root_dir = os.path.dirname(cls.test_root_dir)

        cls.cli_path = os.path.join(cls.root_dir, 'backup', 'cli.py')

    def _call_cli(self, cli_args, stdin=None):
        full_command = [PYTHON_BIN, self.cli_path] + cli_args

        env = os.environ.copy()
        env['PYTHONPATH'] = self.root_dir

        process = Popen(full_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        output = process.communicate(input=stdin)
        return process.returncode, output[0], output[1]

    def test_cli_fails_without_command(self):
        rv, so, se = self._call_cli([])

        self.assertEqual(rv, 1)
        self.assertIn(b'usage: cli.py [-h] ', se)

    def test_cli_fails_with_unknown_command(self):
        rv, so, se = self._call_cli(['unbackup'])

        self.assertEqual(rv, 2)
        self.assertIn(b'invalid choice', se)
