import errno
import os
import shutil
import subprocess

from copy_manager import ICopyManager, DestinationAlreadyExistsError


class RsyncCopyManager(ICopyManager):
    """
    Uses rsync to speed up the transfering process.

    Assumes that the user has taken care of whatever configurations are needed
      to make an rsync operation work with the sender. 
      i.e. if using ssh, the ssh config has been set up for unsupervised
        connecting
      i.e. if using pure rsync, the appropriate credentials have been provided
    """
    def save_game(self, game, force=False):
        self._rsync(game.local_path, game.remote_path, force)

    def load_game(self, game, force=False):
        self._rsync(game.remote_path, game.local_path, force)

    def _rsync(self, src, dst, force):
        if not os.path.exists(src):
            raise OSError(2, 'No such file or directory', src)

        if not force:
            rsync = subprocess.Popen(['rsync', '-ahuHns', '--ignore-existing', '-vvv', src, dst], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            so, se = rsync.communicate()

            print so
            # The block of output from the above function that tells whether or
            #   not files already exist on the remote is during the
            #   `recv_generator` phase. Grab all output around this block of 
            #   lines and check it any of the files we're planning on sending
            #   already exist.
            adding = False
            for line in so.splitlines():
                if line.startswith('recv_generator'):
                    adding = True
                    continue
                if line.startswith('generate_files'):
                    break
                if line.endswith('exists') and adding:
                    raise DestinationAlreadyExistsError('Destination already contains colliding files')

        rsync = subprocess.Popen(['rsync', '-ahuHs', '--no-g', '--no-o', src, dst])
        rsync.wait()
