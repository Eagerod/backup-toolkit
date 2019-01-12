import errno
import os
import shutil

from send2trash import send2trash

from copy_manager import ICopyManager, DestinationAlreadyExistsError


class PureCopyManager(ICopyManager):
    def save_game(self, game, force=False):
        self._copy_directory_to_dest(game.local_path, game.remote_path, force)

    def load_game(self, game, force=False):
        self._copy_directory_to_dest(game.remote_path, game.local_path, force)

    def _copy_directory_to_dest(self, src, dst, force):
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
