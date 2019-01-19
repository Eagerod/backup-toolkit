import argparse
import sys

from ext import get_all_extensions


def do_program():
    parser = argparse.ArgumentParser(description='Backup management tool')

    parser.add_argument('--config', '-c', help='set the location of the configuration yaml')

    subparsers = parser.add_subparsers(dest='command', help='sub-commands')

    cli_extension_classes = {e.get_extension_name(): e for e in get_all_extensions()}
    cli_extensions = {}
    for name, extension in cli_extension_classes.iteritems():
        extension_parser = subparsers.add_parser(name)
        cli_extensions[name] = extension(extension_parser)

    args = parser.parse_args()
    extension = cli_extensions.get(args.command)

    if not extension:
        parser.print_usage(sys.stderr)
        sys.exit(-1)

    extension.run(args)


if __name__ == '__main__':
    do_program()
