import argparse
import sys

from core.extensions import BackupExtension


def do_program():
    parser = argparse.ArgumentParser(description='Backup management tool')

    subparsers = parser.add_subparsers(dest='command', help='sub-commands')

    cli_extension_classes = {e.get_extension_name(): e for e in BackupExtension.get_all_extensions()}
    cli_extensions = {}
    for name, extension in cli_extension_classes.iteritems():
        extension_parser = subparsers.add_parser(name)
        cli_extensions[name] = extension(extension_parser)

    args = parser.parse_args()
    extension = cli_extensions.get(args.command)

    if not extension:  # pragma: no cover (Should be covered by argparse)
        parser.print_usage(sys.stderr)
        sys.exit(1)

    extension.run(args)


if __name__ == '__main__':
    do_program()
