from .copy_manager import DestinationAlreadyExistsError
from .native_copy_manager import NativeCopyManager
from .rsync_copy_manager import RsyncCopyManager


class UnknownCopyManagerError(Exception):
    pass


class CopyManagerFactory(object):
    @classmethod
    def get(cls, manager_name):
        if manager_name in globals():
            return globals()[manager_name]()

        raise UnknownCopyManagerError('Failed to find copy manager: {}'.format(manager_name))


__all__ = [
    'CopyManagerFactory',
    'DestinationAlreadyExistsError',
    'NativeCopyManager',
    'RsyncCopyManager',
    'UnknownCopyManagerError'
]
