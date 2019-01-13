import os

from backup.core.backup_item import BackupItem
from backup.core.copy_managers.rsync_copy_manager import RsyncCopyManager

from copy_manager_test_case import CopyManagerTestCase


class RsyncCopyManagerTestCase(CopyManagerTestCase):
    @classmethod
    def setUpClass(cls):
        super(RsyncCopyManagerTestCase, cls).setUpClass()

        cls.copy_manager = RsyncCopyManager()

    # Rsync only cares if the destination directory exists, and there are files
    #   present that would cause an issue.
    def test_copy_directory_dest_exists(self):
        backup_item = BackupItem(self.source_dir, self.dest_dir)

        self.copy_manager.save_item(backup_item)

        dest_filename = os.path.join(self.source_dir, os.path.basename(self.source_file.name))

        with open(dest_filename) as f:
            self.assertEqual(f.read(), self.expected_content)
