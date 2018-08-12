import os

from game import Game


class GameNotFoundError(Exception):
    pass


class GamesManager(object):
    def __init__(self, platform, game_definitions=(), platform_remote=None, path_variables=None):
        self.platform = platform
        self._game_aliases = {}

        self.has_games = False
        self._resolve_definitions(game_definitions, platform_remote, path_variables)

    def _resolve_definitions(self, game_definitions, platform_remote=None, path_variables=None):
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
            paths['local'] = os.path.expanduser(paths['local'])

            if 'remote' in paths:
                paths['remote'] = os.path.expanduser(paths['remote'])
            else:
                paths['remote'] = '$REMOTE_ROOT'

            if platform_remote:
                paths['remote'] = paths['remote'].replace('$REMOTE_ROOT', os.path.expanduser(platform_remote))

            if path_variables:
                paths['local'] = paths['local'].format(**path_variables)
                paths['remote'] = paths['remote'].format(**path_variables)

            self._game_aliases[game['name'].lower()] = paths
            for alias in game.get('aliases', []):
                self._game_aliases[alias.lower()] = paths

    def resolve_alias(self, alias):
        if not alias:
            raise GameNotFoundError('No game name provided')

        alias = alias.lower()

        if alias not in self._game_aliases:
            raise GameNotFoundError('No game found with that name')

        return Game(**self._game_aliases[alias])
