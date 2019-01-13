import errno
import os
import shutil

from send2trash import send2trash

from copy_manager import ICopyManager, DestinationAlreadyExistsError


class NativeCopyManager(ICopyManager):
    def save_item(self, backup_item, force=False):
        self._copy_directory_to_dest(backup_item.local_path, backup_item.remote_path, force)

    def load_item(self, backup_item, force=False):
        self._copy_directory_to_dest(backup_item.remote_path, backup_item.local_path, force)

    def _copy_directory_to_dest(self, src, dst, force):
        """Copy a file using native Python APIs

        Positional arguments:
            src -- source file path
            dst -- destination file path
            force -- Overwrite existing files if present.
        """
        if not os.path.exists(src):
            raise OSError(2, 'No such file or directory', src)

        if force and os.path.exists(dst):
            send2trash(dst)

        dst_dirname = os.path.dirname(dst)

        try:
            os.makedirs(dst_dirname)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(dst_dirname):
                pass
            else:
                raise

        try:
            shutil.copytree(src, dst)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise DestinationAlreadyExistsError('Destination already contains colliding files')
            raise
