from unittest import TestCase

from backup.core.copy_managers import CopyManagerFactory, UnknownCopyManagerError


class CopyManagerFactoryTestCase(TestCase):
    def test_get(self):
        native = CopyManagerFactory.get('NativeCopyManager')
        rsync = CopyManagerFactory.get('RsyncCopyManager')

        self.assertNotEqual(native, rsync)

    def test_get_does_not_exist(self):
        with self.assertRaises(UnknownCopyManagerError) as exc:
            CopyManagerFactory.get('RaisesExceptionCopyManager')

        self.assertEqual(exc.exception.args, ('Failed to find copy manager: RaisesExceptionCopyManager',))
