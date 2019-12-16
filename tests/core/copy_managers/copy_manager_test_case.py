import os
import tempfile
import shutil
from unittest import TestCase

from backup.core.backup_item import BackupItem
from backup.core.copy_managers.copy_manager import DestinationAlreadyExistsError


def skip_if_base_class(fn):
    def wrapper(self, *args, **kwargs):
        if type(self) == CopyManagerTestCase:
            return self.skipTest('This test class is abstract. Tests are skipped.')
        return fn(self, *args, **kwargs)
    return wrapper


class CopyManagerTestCase(TestCase):
    """Base class for testing any CopyManager. All required test cases will be
    implemented in this base class, and subclasses are welcome to set their own
    CopyManager subclass to be tested.
    """
    @classmethod
    def setUpClass(cls):
        super(CopyManagerTestCase, cls).setUpClass()
        cls.copy_manager = None

        cls.expected_content = 'This is example content for comparison.\n'

    def setUp(self):
        super(CopyManagerTestCase, self).setUp()

        if not self.copy_manager and type(self) != CopyManagerTestCase:
            raise Exception('Subclasses must set a copy_manager in setUpClass')

        self.source_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()

        self.source_file = tempfile.NamedTemporaryFile(dir=self.source_dir, delete=False)
        self.source_file.write(self.expected_content.encode())
        self.source_file.close()

    def tearDown(self):
        super(CopyManagerTestCase, self).tearDown()

        if os.path.exists(self.source_dir):
            shutil.rmtree(self.source_dir)
        if os.path.exists(self.dest_dir):
            shutil.rmtree(self.dest_dir)

    @skip_if_base_class
    def test_save_item_directory_success(self):
        shutil.rmtree(self.dest_dir)

        backup_item = BackupItem(self.source_dir, self.dest_dir)

        self.copy_manager.save_item(backup_item)

        dest_filename = os.path.join(self.source_dir, os.path.basename(self.source_file.name))

        with open(dest_filename) as f:
            self.assertEqual(f.read(), self.expected_content)

    @skip_if_base_class
    def test_save_item_directory_dest_exists(self):
        shutil.copy(self.source_file.name, self.dest_dir)

        backup_item = BackupItem(self.source_dir, self.dest_dir)

        with self.assertRaises(DestinationAlreadyExistsError) as exc:
            self.copy_manager.save_item(backup_item)

        self.assertEqual(exc.exception.args, ('Destination already contains colliding files',))

    @skip_if_base_class
    def test_save_item_directory_dest_exists_force(self):
        shutil.copy(self.source_file.name, self.dest_dir)

        backup_item = BackupItem(self.source_dir, self.dest_dir)

        self.copy_manager.save_item(backup_item, force=True)

        dest_filename = os.path.join(self.source_dir, os.path.basename(self.source_file.name))

        with open(dest_filename) as f:
            self.assertEqual(f.read(), self.expected_content)

    @skip_if_base_class
    def test_save_item_source_does_not_exist(self):
        shutil.rmtree(self.source_dir)

        backup_item = BackupItem(self.source_dir, self.dest_dir)

        with self.assertRaises(OSError) as exc:
            self.copy_manager.save_item(backup_item)

        self.assertEqual(exc.exception.args, (2, 'No such file or directory'))
        self.assertEqual(exc.exception.filename, self.source_dir)

    @skip_if_base_class
    def test_load_item(self):
        shutil.rmtree(self.dest_dir)

        backup_item = BackupItem(self.dest_dir, self.source_dir)

        self.copy_manager.load_item(backup_item)

        dest_filename = os.path.join(self.source_dir, os.path.basename(self.source_file.name))

        with open(dest_filename) as f:
            self.assertEqual(f.read(), self.expected_content)
