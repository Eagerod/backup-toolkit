import os

from .game import Game


class GameNotFoundError(Exception):
    pass


class GamesManager(object):
    def __init__(self, platform, game_definitions=()):
        self.platform = platform
        self._game_aliases = {}

        self.has_games = False
        self._resolve_definitions(game_definitions)

    def _resolve_definitions(self, game_definitions):
        for game in game_definitions:
            # If this game hasn't been configured for this platform, or just
            #   plain old doesn't exist on this platform, skip it.
            if self.platform not in game:
                continue
            self.has_games = True

            # Get the appropriate paths for this platform
            paths = game[self.platform]

            # Allow for the remote path to be fully excluded. If that's the
            #   case, just use the remote root.
            if 'remote' not in paths:
                paths['remote'] = '$REMOTE_ROOT'

            paths['remote'] = os.path.expanduser(os.path.expandvars(paths['remote']))
            paths['local'] = os.path.expanduser(os.path.expandvars(paths['local']))

            self._game_aliases[game['name'].lower()] = paths
            for alias in game.get('aliases', []):
                self._game_aliases[alias.lower()] = paths

    def resolve_alias(self, alias):
        if not alias:
            raise GameNotFoundError('No game name provided')

        alias = alias.lower()

        if alias not in self._game_aliases:
            raise GameNotFoundError('No game found with that name')

        return Game(local_path=self._game_aliases[alias]['local'], remote_path=self._game_aliases[alias]['remote'])
