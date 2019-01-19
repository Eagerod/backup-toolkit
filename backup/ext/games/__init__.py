import os
import platform
import sys

import yaml
from core import copy_managers
from core.copy_managers import DestinationAlreadyExistsError
from core.extensions import BackupExtension

from games_manager import GamesManager, GameNotFoundError

DEFAULT_CONFIG_YAML_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')


class InvalidConfigError(Exception):
    pass


class NoGamesDefinedError(Exception):
    pass


class PlatformNotFoundError(Exception):
    pass


class GameSavesCliOptions(object):
    SAVE = 'save'
    LOAD = 'load'


class Extension(BackupExtension):
    GAMES_BACKUP_SUBCOMMAND_NAME = 'games'

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

        saves_subparsers = self.parser.add_subparsers(dest='operation', help='operation')

        ssp = saves_subparsers.add_parser(GameSavesCliOptions.SAVE,
                                          help='save the selected game to the remote backup location')
        slp = saves_subparsers.add_parser(GameSavesCliOptions.LOAD,
                                          help='load the selected game to this machine')

        ssp.add_argument('--all', '-a', action='store_true', help='Copy all local games to the remote')
        ssp.add_argument('--game', '-g', help='select the game, or an alias to run the command against')
        ssp.add_argument('--force', '-f', action='store_true', help='replace existing destination files if present')

        slp.add_argument('--game', '-g', help='select the game, or an alias to run the command against')
        slp.add_argument('--force', '-f', action='store_true', help='replace existing destination files if present')

    @classmethod
    def get_extension_name(cls):
        return cls.GAMES_BACKUP_SUBCOMMAND_NAME

    def run(self, args):
        try:
            save_game_cli = SaveGameCli(args.config)
        except (PlatformNotFoundError, NoGamesDefinedError, InvalidConfigError) as e:
            print >> sys.stderr, e.message
            self.parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            if args.operation == GameSavesCliOptions.SAVE:
                if args.all:
                    save_game_cli.save_all_games(args.force)
                else:
                    save_game_cli.save_game(args.game, args.force)
            elif args.operation == GameSavesCliOptions.LOAD:
                save_game_cli.load_game(args.game, args.force)
            else:  # pragma: no cover
                # Shouldn't actually be reachable, but a good failsafe in case commands are added to the list without
                # actually being implemented.
                self.parser.print_usage(sys.stderr)
                sys.exit(2)
        except GameNotFoundError as e:
            print >> sys.stderr, e.message
            self.parser.print_usage(sys.stderr)
            sys.exit(3)
        except OSError as e:
            action_name = 'backup' if args.operation == GameSavesCliOptions.SAVE else 'restore'
            print >> sys.stderr, 'Cannot {} save games because: {}'.format(action_name, e)
            sys.exit(4)
        except DestinationAlreadyExistsError as e:
            action_name = 'backup' if args.operation == GameSavesCliOptions.SAVE else 'restore'
            print >> sys.stderr, 'Cannot {} save games because: {}'.format(action_name, e)
            sys.exit(5)
        except (KeyboardInterrupt, EOFError):
            print >> sys.stderr, ''
            sys.exit(6)


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
            raise NoGamesDefinedError('No game definitions found in {}'.format(config_filepath))

        platform_system = platform.system()
        if platform_system == 'Darwin':
            plat_key = 'osx'
        elif platform_system == 'Windows':
            plat_key = 'windows'
        elif platform_system.lower().startswith('cygwin'):
            plat_key = 'cygwin'
        else:
            raise PlatformNotFoundError('Running on unknown platform, paths may be incorrect')

        # Set up a `REMOTE_ROOT` environment variable so that the remote can
        #   be added by just evaluating the environment, rather than needing
        #   to pass around variables everywhere. If this is already present in
        #   the environment, use it as is.
        if 'REMOTE_ROOT' not in os.environ and 'remotes' in config and plat_key in config['remotes']:
            os.environ['REMOTE_ROOT'] = config['remotes'][plat_key]
        elif 'REMOTE_ROOT' not in os.environ:
            raise InvalidConfigError('Cannot set up remote for this platform')

        # Prepare variables for use by expanding out existing environment
        #   variables into them, then set them into the environment, but like
        #   above, skip ones that already exist, so the user can set them
        #   themselves if they want them.
        for k, v in config.get('variables', {}).iteritems():
            if k in os.environ:
                continue

            os.environ[k] = os.path.expandvars(v)

        self.games_manager = GamesManager(plat_key, self.game_definitions)

        if not self.games_manager.has_games:
            raise NoGamesDefinedError('There are no games configured for this platform')

        if not hasattr(copy_managers, config['manager']):
            raise InvalidConfigError('Failed to find manager class {}'.format(config['manager']))

        manager_class = getattr(copy_managers, config['manager'])
        self.copy_manager = manager_class()

    def save_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self.copy_manager.save_item(game, force)

    def load_game(self, alias=None, force=False):
        game = self._get_game(alias)
        self.copy_manager.load_item(game, force)

    def save_all_games(self, force=False):
        for game in self.game_definitions:
            try:
                self.copy_manager.save_item(self._get_game(game['name']), force)
            except GameNotFoundError:
                pass

    def _get_game(self, alias=None):
        try:
            return self.games_manager.resolve_alias(alias)
        except GameNotFoundError as e:
            raise GameNotFoundError(e.message + self._error_help_text()), None, sys.exc_info()[2]

    def _format_game_name(self, game):
        if 'aliases' in game:
            return '{} ({})'.format(game['name'], ', '.join(game['aliases']))
        return game['name']

    def _error_help_text(self):
        game_names = []
        for g in self.game_definitions:
            try:
                self.games_manager.resolve_alias(g['name'])
                game_names.append(self._format_game_name(g))
            except GameNotFoundError:
                pass

        ret = '\n'.join(['  {}'.format(g) for g in game_names])
        if not ret.strip():
            return '\nThere are no games configured for this platform'
        return '\nTry one of the following:\n{}'.format('\n'.join(['  {}'.format(g) for g in game_names]))


__all__ = ['Extension']
