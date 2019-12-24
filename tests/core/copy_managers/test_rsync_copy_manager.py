import os
import shutil

from backup.core.backup_item import BackupItem
from backup.core.copy_managers import DestinationAlreadyExistsError
from backup.core.copy_managers.rsync_copy_manager import RsyncCopyManager

from .copy_manager_test_case import CopyManagerTestCase


class RsyncCopyManagerTestCase(CopyManagerTestCase):
    @classmethod
    def setUpClass(cls):
        super(RsyncCopyManagerTestCase, cls).setUpClass()

        cls.copy_manager = RsyncCopyManager()

    def test_save_item_directory_dest_exists(self):
        # With the paths generated, rsync copies the source directory into the
        #   destination directory. In order to produce a collision, the whole
        #   source directory must be present.
        shutil.copytree(self.source_dir, os.path.join(self.dest_dir, os.path.basename(self.source_dir)))

        backup_item = BackupItem(self.source_dir, self.dest_dir)

        with self.assertRaises(DestinationAlreadyExistsError) as exc:
            self.copy_manager.save_item(backup_item)

        self.assertEqual(exc.exception.args, ('Destination already contains colliding files',))
