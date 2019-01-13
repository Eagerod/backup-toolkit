class DestinationAlreadyExistsError(Exception):
    pass


class ICopyManager(object):
    """
    The copy manager interface is provided as a means of defining what each
    copy class must implement.
    """
    def save_item(self, backup_item, force=False):
        """Copy an item to the remote.

        Positional arguments:
            backup_item -- The backup.core.backup_item.BackupItem that will be
                copied to its remote path

        Keyword arguments:
            force -- Use this tool's force mechanism to overwrite files that
                already exist on the remote (default False)
        """
        raise NotImplementedError

    def load_item(self, backup_item, force=False):
        """Load an item from the remote.

        Positional arguments:
            backup_item -- The backup.core.backup_item.BackupItem that will be
                copied to its local path

        Keyword arguments:
            force -- Use this tool's force mechanism to overwrite files that
                already exist locally (default False)
        """
        raise NotImplementedError
