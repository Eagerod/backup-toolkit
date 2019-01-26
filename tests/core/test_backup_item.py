from unittest import TestCase

from backup.core.backup_item import BackupItem


class BackupItemTestCase(TestCase):
    def test_creation(self):
        b = BackupItem('local', 'remote')

        self.assertEqual(b.local_path, 'local')
        self.assertEqual(b.remote_path, 'remote')

    def test_comparrison(self):
        b1 = BackupItem('local', 'remote')
        b2 = BackupItem('local', 'remote')
        b3 = BackupItem('remote', 'local')
        b4 = 7

        self.assertEqual(b1, b1)
        self.assertEqual(b1, b2)
        self.assertNotEqual(b1, b3)
        self.assertNotEqual(b2, b3)
        self.assertNotEqual(b1, b4)
