from backup.core.copy_managers.native_copy_manager import NativeCopyManager

from copy_manager_test_case import CopyManagerTestCase


class NativeCopyManagerTestCase(CopyManagerTestCase):
    @classmethod
    def setUpClass(cls):
        super(NativeCopyManagerTestCase, cls).setUpClass()

        cls.copy_manager = NativeCopyManager()
