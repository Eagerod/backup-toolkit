import os

from game import Game


class GameNotFoundError(Exception):
    pass


class GamesManager(object):
    def __init__(self, platform, game_definitions=(), platform_remote=None):
        self.platform = platform
        self._game_aliases = {}

        self._resolve_definitions(game_definitions, platform_remote)

    def _resolve_definitions(self, game_definitions, platform_remote=None):
        for game in game_definitions:
            # Get the appropriate paths for this platform
            paths = game[self.platform]

            paths['local'] = os.path.expanduser(paths['local'])
            paths['remote'] = os.path.expanduser(paths['remote'])

            if platform_remote:
                paths['remote'] = paths['remote'].replace('$REMOTE_ROOT', os.path.expanduser(platform_remote))

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
