from unittest import TestCase

from backup.core.extensions import BackupExtension


class ExtensionsTestCase(TestCase):
    def test_get_all_extensions(self):
        extensions = BackupExtension.get_all_extensions()

        self.assertEqual(len(extensions), 1)

    def test_get_system_platform_this_platform_supported(self):
        p = BackupExtension.get_system_platform()
        self.assertIsNotNone(p)
