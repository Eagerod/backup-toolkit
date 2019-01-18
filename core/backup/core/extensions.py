class BackupExtension(object):
    def __init__(self, cli_parser):
        self.parser = cli_parser

    @classmethod
    def get_extension_name(cls):
        raise NotImplementedError

    def run(self, args):
        raise NotImplementedError
