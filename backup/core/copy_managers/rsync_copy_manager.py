import os
import subprocess

from copy_manager import ICopyManager, DestinationAlreadyExistsError


class RsyncCopyManager(ICopyManager):
    """
    Uses rsync to speed up the transferring process.

    Assumes that the user has taken care of whatever configurations are needed
      to make an rsync operation work with the sender.
      i.e. if using ssh, the ssh config has been set up for unsupervised
        connecting
      i.e. if using pure rsync, the appropriate credentials have been provided
    """
    def save_item(self, backup_item, force=False):
        self._rsync(backup_item.local_path, backup_item.remote_path, force)

    def load_item(self, backup_item, force=False):
        self._rsync(backup_item.remote_path, backup_item.local_path, force)

    def _rsync(self, src, dst, force):
        if not os.path.exists(src):
            raise OSError(2, 'No such file or directory', src)

        if not force:
            rsync = subprocess.Popen(
                ['rsync', '-ahuHs', '--dry-run', '--ignore-existing', '-vvv', src, dst],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            so, se = rsync.communicate()

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
