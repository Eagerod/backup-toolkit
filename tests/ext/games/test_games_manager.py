from unittest import TestCase

from backup.ext.games.game import Game
from backup.ext.games.games_manager import GamesManager, GameNotFoundError


THIS_MACHINE_SIMULATED_PLATFORM = 'some_platform'
OTHER_MACHINE_SIMULATED_PLATFORM = 'some_other_platform'


class GamesManagerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(GamesManagerTestCase, cls).setUpClass()

        cls.source_dir = 'some_dirname'
        cls.dest_dir = 'some_dest_dirname'

        cls.game_1_platform_dict = {
            'local': cls.source_dir,
            'remote': cls.dest_dir
        }
        cls.game_2_platform_dict = {
            'local': cls.source_dir + 'empty',
            'remote': '$REMOTE_ROOT'
        }

        cls.game_definitions = [
            {
                'name': 'game1',
                'aliases': [
                    'g1'
                ],
                THIS_MACHINE_SIMULATED_PLATFORM: {
                    'local': cls.source_dir,
                    'remote': cls.dest_dir
                },
                OTHER_MACHINE_SIMULATED_PLATFORM: {
                    'local': cls.source_dir + 'loljk',
                    'remote': cls.dest_dir + 'loljk'
                }
            },
            {
                'name': 'game2',
                'aliases': [
                    'g2'
                ],
                THIS_MACHINE_SIMULATED_PLATFORM: {
                    'local': cls.source_dir + 'empty',
                }
            },
            {
                'name': 'game3',
                'aliases': [
                    'g3'
                ],
                OTHER_MACHINE_SIMULATED_PLATFORM: {
                    'local': cls.source_dir + 'jklol',
                    'remote': cls.dest_dir + 'jklol'
                }
            }
        ]

        cls.parsed_game_1 = Game(cls.source_dir, cls.dest_dir)
        cls.parsed_game_2 = Game(cls.source_dir + 'empty', '$REMOTE_ROOT')

    def test_init(self):
        gm = GamesManager(THIS_MACHINE_SIMULATED_PLATFORM, self.game_definitions)

        self.assertTrue(gm.has_games)
        self.assertEqual(gm.platform, THIS_MACHINE_SIMULATED_PLATFORM)
        self.assertEqual(gm._game_aliases, {
            'game1': self.game_1_platform_dict,
            'g1': self.game_1_platform_dict,
            'game2': self.game_2_platform_dict,
            'g2': self.game_2_platform_dict
        })

    def test_resolve_alias(self):
        gm = GamesManager(THIS_MACHINE_SIMULATED_PLATFORM, self.game_definitions)

        self.assertEqual(gm.resolve_alias('game1'), self.parsed_game_1)
        self.assertEqual(gm.resolve_alias('g1'), self.parsed_game_1)
        self.assertEqual(gm.resolve_alias('game2'), self.parsed_game_2)
        self.assertEqual(gm.resolve_alias('g2'), self.parsed_game_2)

    def test_resolve_alias_empty_alias(self):
        gm = GamesManager(THIS_MACHINE_SIMULATED_PLATFORM, self.game_definitions)

        with self.assertRaises(GameNotFoundError) as exc:
            gm.resolve_alias('')

        self.assertEqual(exc.exception.args, ('No game name provided',))

    def test_resolve_alias_does_not_exist(self):
        gm = GamesManager(THIS_MACHINE_SIMULATED_PLATFORM, self.game_definitions)

        with self.assertRaises(GameNotFoundError) as exc:
            gm.resolve_alias('game3')

        self.assertEqual(exc.exception.args, ('No game found with that name',))
