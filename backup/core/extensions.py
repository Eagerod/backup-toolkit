import imp  # noqa: Needed for importlib to work
import importlib
import os
import platform
import sys
from inspect import getmembers


EXTENSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ext')


class PlatformNotFoundError(Exception):
    pass


class _SysPathTemp(object):
    def __init__(self, path):
        self.path = path
        self.added_path = False

    def __enter__(self):
        if self.path not in sys.path:
            sys.path.insert(0, self.path)
            self.added_path = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.added_path and self.path in sys.path:
            sys.path.remove(self.path)


class BackupExtension(object):
    class Platform(object):
        DARWIN = 'osx'
        WINDOWS = 'windows'
        CYGWIN = 'cygwin'
        LINUX = 'linux'

    def __init__(self, cli_parser):
        self.parser = cli_parser

    @classmethod
    def get_all_extensions(cls):
        """Search through all folders within the directory this script is
        contained in, and return any extensions that are found.
        """
        extensions = []
        for maybe_dir in os.listdir(EXTENSIONS_DIR):
            module_path = os.path.join(EXTENSIONS_DIR, maybe_dir)
            if os.path.isdir(module_path):
                try:
                    module_init = os.path.join(module_path, '__init__.py')
                    if not os.path.exists(module_init):
                        continue

                    with _SysPathTemp(module_path):
                        mod_name = 'ext.{}'.format(maybe_dir)
                        spec = importlib.util.spec_from_file_location(mod_name, module_init)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        for member_name, member in getmembers(module, lambda o: type(o) == type):
                            if member_name == 'Extension':
                                extensions.append(member)
                except ImportError as e:  # pragma: no cover
                    print(e)
                    pass

        return extensions

    @classmethod
    def get_system_platform(cls):
        """Any extension that's implementing a task may have to do so on
        different platforms. This method returns the key used to identify
        platforms.
        """
        platform_system = platform.system().lower()
        if platform_system == 'darwin':  # pragma: no cover
            platform_name = cls.Platform.DARWIN
        elif platform_system == 'windows':  # pragma: no cover
            platform_name = cls.Platform.WINDOWS
        elif platform_system == 'linux':  # pragma: no cover
            platform_name = cls.Platform.LINUX
        elif platform_system.startswith('cygwin'):  # pragma: no cover
            platform_name = cls.Platform.CYGWIN
        else:  # pragma: no cover
            raise PlatformNotFoundError(
                'Running on unknown platform ({}), paths may be incorrect'.format(platform_system))

        return platform_name

    @classmethod
    def get_extension_name(cls):
        raise NotImplementedError

    def run(self, args):
        raise NotImplementedError
