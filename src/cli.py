import argparse
import errno
import os
import platform
import shutil
import sys

import yaml
from send2trash import send2trash


DEFAULT_GAMES_YAML_FILEPATH = os.path.join(os.path.dirname(__file__), 'games.yaml')
DEFAULT_CONFIG_YAML_FILEPATH = os.path.join(os.path.dirname(__file__), 'config.yaml')


class NoGamesDefinedError(Exception):
    pass


class GameNotFoundError(Exception):
    pass


class PlatformNotFoundError(Exception):
    pass


class SaveGameCliOptions(object):
    SAVE = 'save'
    LOAD = 'load'


class SaveGameCli(object):
    def __init__(self, games_filepath=None, config_filepath=None):
        if games_filepath is None:
            games_filepath = DEFAULT_GAMES_YAML_FILEPATH

        if config_filepath is None:
            config_filepath = DEFAULT_CONFIG_YAML_FILEPATH

        with open(games_filepath) as f:
            self.game_definitions = yaml.load(f.read())

        if not self.game_definitions:
            raise NoGamesDefinedError('No game definitions found in {}'.format(games_filepath))

        with open(config_filepath) as f:
            config = yaml.load(f.read())

        platform_system = platform.system()

        self.aliases = {}
        for game in self.game_definitions:
            # Get the appropriate paths for this platform
            if platform_system == 'Darwin':
                plat_key = 'osx'
            elif platform_system == 'Windows':
                plat_key = 'windows'
            else:
                raise PlatformNotFoundError('Running on unknown platform, paths may be incorrect')

            paths = game[plat_key]

            paths['local'] = os.path.expanduser(paths['local'])
            paths['remote'] = os.path.expanduser(paths['remote'])

            if 'remotes' in config:
                paths['remote'] = os.path.abspath(
                    paths['remote'].replace('$REMOTE_ROOT', os.path.expanduser(config['remotes'][plat_key]))
                )

            self.aliases[game['name'].lower()] = paths
            for alias in game.get('aliases', []):
                self.aliases[alias.lower()] = paths

    def save_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self._copy_directory_to_dest(game['local'], game['remote'], force)

    def load_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self._copy_directory_to_dest(game['remote'], game['local'], force)

    def _get_game(self, alias=None):
        if not alias:
            err_msg = 'No game name provided. Try one of the following:\n{}'.format(
                '\n'.join('  {}'.format(self._format_game_name(g)) for g in self.game_definitions)
            )
            raise GameNotFoundError(err_msg)

        alias = alias.lower()

        if alias not in self.aliases:
            err_msg = 'No game found with that name. Try one of the following:\n{}'.format(
                '\n'.join('  {}'.format(self._format_game_name(g)) for g in self.game_definitions)
            )
            raise GameNotFoundError(err_msg)

        return self.aliases[alias]

    def _format_game_name(self, game):
        if 'aliases' in game:
            return '{} ({})'.format(game['name'], ', '.join(game['aliases']))
        return game['name']

    def _copy_directory_to_dest(self, src, dst, force):
        if not os.path.exists(src):
            raise OSError(2, 'No such file or directory', src)

        if force and os.path.exists(dst):
            send2trash(dst)

        dst_dirname = os.path.dirname(dst)
        
        try:
            os.makedirs(dst_dirname)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dst_dirname):
                pass
            else:
                raise

        shutil.copytree(src, dst)


def do_program():
    parser = argparse.ArgumentParser(description='Save game synchronization command line tool')

    parser.add_argument('--game', '-g', help='select the game, or an alias to run the command against')
    parser.add_argument('--force', '-f', action='store_true', help='delete existing destination directory if present')

    parser.add_argument('--games', '-G', help='set the location of the games definition yaml')
    parser.add_argument('--config', '-C', help='set the location of the configuration yaml')

    subparsers = parser.add_subparsers(dest='command', help='sub-commands')

    subparsers.add_parser(SaveGameCliOptions.SAVE, help='save the selected game to the remote backup location')
    subparsers.add_parser(SaveGameCliOptions.LOAD, help='load the selected game to this machine')

    args = parser.parse_args()

    try:
        save_game_cli = SaveGameCli(args.games, args.config)

        if args.command == SaveGameCliOptions.SAVE:
            save_game_cli.save_game(args.game, args.force)
        elif args.command == SaveGameCliOptions.LOAD:
            save_game_cli.load_game(args.game, args.force)
        else:  # pragma: no cover
            # Shouldn't actually be reachable, but a good failsafe in case commands are added to the list without
            # actually being implemented.
            parser.print_usage(sys.stderr)
            sys.exit(-1)
    except (GameNotFoundError, PlatformNotFoundError, NoGamesDefinedError) as e:
        print >> sys.stderr, e.message
        sys.exit(-1)
    except OSError as e:
        print >> sys.stderr, 'Cannot backup save games because: {}'.format(e)
        sys.exit(-1)
    except (KeyboardInterrupt, EOFError):
        print >> sys.stderr, ''
        sys.exit(-1)


if __name__ == '__main__':
    do_program()
