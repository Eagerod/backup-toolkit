class BackupItem(object):
    def __init__(self, local_path, remote_path):
        self.local_path = local_path
        self.remote_path = remote_path

    def __eq__(self, other):
        if not issubclass(type(other), BackupItem):
            return False

        return self.local_path == other.local_path and self.remote_path == other.remote_path
