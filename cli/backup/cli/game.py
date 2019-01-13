from backup_item import BackupItem

class Game(BackupItem):
    def __init__(self, local, remote):
        self.local_path = local
        self.remote_path = remote
