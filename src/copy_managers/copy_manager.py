class DestinationAlreadyExistsError(Exception):
    pass


class ICopyManager(object):
    """
    The copy manager interface is provided as a means of defining what each
    copy class must implement.
    """
    def save_game(self, game, force=False):
        """
        Write a game's save files to the appropriate location for this platform.
        """
        raise NotImplementedError

    def load_game(self, game, force=False):
        """
        Load a game's save files from its remote saving location.
        """
        raise NotImplementedError
