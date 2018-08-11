import argparse
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml

from copy_managers import PureCopyManager
from games_manager import GamesManager, GameNotFoundError


DEFAULT_CONFIG_YAML_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')


class NoGamesDefinedError(Exception):
    pass


class PlatformNotFoundError(Exception):
    pass


class SaveGameCliOptions(object):
    SAVE = 'save'
    LOAD = 'load'


class SaveGameCli(object):
    def __init__(self, config_filepath=None):
        """
        Construct the CLI facade, proxying whatever it needs to the appropriate
        game and copy managers.
        """
        if config_filepath is None:
            config_filepath = DEFAULT_CONFIG_YAML_FILEPATH

        with open(config_filepath) as f:
            config = yaml.load(f.read())

        self.game_definitions = config['games']
        if not self.game_definitions:
            raise NoGamesDefinedError('No game definitions found in {}'.format(games_filepath))

        platform_system = platform.system()
        if platform_system == 'Darwin':
            plat_key = 'osx'
        elif platform_system == 'Windows':
            plat_key = 'windows'
        else:
            raise PlatformNotFoundError('Running on unknown platform, paths may be incorrect')

        platform_remote = None
        if 'remotes' in config and plat_key in config['remotes']:
            platform_remote = config['remotes'][plat_key]

        self.games_manager = GamesManager(plat_key, self.game_definitions, platform_remote)
        self.copy_manager = PureCopyManager()

    def save_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self.copy_manager.save_game(game, force)

    def load_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self.copy_manager.load_game(game, force)

    def _get_game(self, alias=None):
        try:
            return self.games_manager.resolve_alias(alias)
        except GameNotFoundError as e:
            raise GameNotFoundError(e.message + ' Try one of the following:\n{}'.format(
                '\n'.join('  {}'.format(self._format_game_name(g)) for g in self.game_definitions)
            )), None, sys.exc_info()[2]

    def _format_game_name(self, game):
        if 'aliases' in game:
            return '{} ({})'.format(game['name'], ', '.join(game['aliases']))
        return game['name']


def do_program():
    parser = argparse.ArgumentParser(description='Save game synchronization command line tool')

    parser.add_argument('--config', '-c', help='set the location of the configuration yaml')

    subparsers = parser.add_subparsers(dest='command', help='sub-commands')

    sp = subparsers.add_parser(SaveGameCliOptions.SAVE, help='save the selected game to the remote backup location')
    lp = subparsers.add_parser(SaveGameCliOptions.LOAD, help='load the selected game to this machine')

    sp.add_argument('--game', '-g', help='select the game, or an alias to run the command against')
    sp.add_argument('--force', '-f', action='store_true', help='delete existing destination directory if present')

    lp.add_argument('--game', '-g', help='select the game, or an alias to run the command against')
    lp.add_argument('--force', '-f', action='store_true', help='delete existing destination directory if present')

    args = parser.parse_args()

    try:
        save_game_cli = SaveGameCli(args.config)
    except (PlatformNotFoundError, NoGamesDefinedError) as e:
        print >> sys.stderr, e.message
        sys.exit(-1)

    try:
        if args.command == SaveGameCliOptions.SAVE:
            save_game_cli.save_game(args.game, args.force)
        elif args.command == SaveGameCliOptions.LOAD:
            save_game_cli.load_game(args.game, args.force)
        else:  # pragma: no cover
            # Shouldn't actually be reachable, but a good failsafe in case commands are added to the list without
            # actually being implemented.
            parser.print_usage(sys.stderr)
            sys.exit(-1)
    except GameNotFoundError as e:
        print >> sys.stderr, e.message
        sys.exit(-1)
    except OSError as e:
        action_name = 'backup' if args.command == SaveGameCliOptions.SAVE else 'restore'
        print >> sys.stderr, 'Cannot {} save games because: {}'.format(action_name, e)
        sys.exit(-1)
    except (KeyboardInterrupt, EOFError):
        print >> sys.stderr, ''
        sys.exit(-1)


if __name__ == '__main__':
    do_program()
