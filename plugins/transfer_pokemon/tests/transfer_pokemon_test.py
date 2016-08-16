import unittest

from mock import Mock

from api.pokemon import Pokemon
from plugins.transfer_pokemon import TransferPokemon
from pokemongo_bot import EventManager
from pokemongo_bot.tests import create_mock_bot


class TransferPokemonPluginTest(unittest.TestCase):

    def test_wrap_pokemon(self):
        event_manager = EventManager()
        logger = Mock()
        logger.log = Mock()
        transfer_plugin = TransferPokemon(
            {
                'transfer_on_start': False
            },
            event_manager,
            logger
        )

        transfer_list = [self._create_pokemon(unique_id=1)]
        transfer_list = transfer_plugin.wrap_pokemon_in_list(transfer_list=transfer_list, pokemon=self._create_pokemon(unique_id=2))["transfer_list"]
        assert len(transfer_list) == 2
        assert transfer_list[0].unique_id == 1
        assert transfer_list[1].unique_id == 2

    def test_deployed_pokemon_filter(self):
        event_manager = EventManager()
        logger = Mock()
        logger.log = Mock()
        transfer_plugin = TransferPokemon(
            {
                'transfer_on_start': False
            },
            event_manager,
            logger
        )

        bot = create_mock_bot()

        transfer_list = [self._create_pokemon(unique_id=1, deployed=True),
                         self._create_pokemon(unique_id=2, deployed=True),
                         self._create_pokemon(unique_id=3, deployed=True),
                         self._create_pokemon(unique_id=4, deployed=False),
                         self._create_pokemon(unique_id=5, deployed=True),
                         self._create_pokemon(unique_id=6, deployed=False)]

        result_dict = transfer_plugin.filter_deployed_pokemon(bot=bot, transfer_list=transfer_list)
        filtered_list = result_dict["transfer_list"]
        assert len(filtered_list) == 2
        assert filtered_list[0].unique_id == 4
        assert filtered_list[1].unique_id == 6
        assert result_dict["filter_list"][0] == "excluding Pokemon at gyms"

        transfer_list = [self._create_pokemon(deployed=False)]
        result_dict = transfer_plugin.filter_deployed_pokemon(bot=bot, transfer_list=transfer_list)
        assert len(result_dict["transfer_list"]) == 1
        assert len(result_dict["filter_list"]) == 0

        self.set_empty_inventory(bot)
        assert transfer_plugin.filter_deployed_pokemon(bot=bot) is False

    def test_favorited_pokemon_filter(self):
        event_manager = EventManager()
        logger = Mock()
        logger.log = Mock()
        transfer_plugin = TransferPokemon(
            {
                'transfer_on_start': False
            },
            event_manager,
            logger
        )

        bot = create_mock_bot()

        transfer_list = [self._create_pokemon(unique_id=1, favorite=True),
                         self._create_pokemon(unique_id=2, favorite=True),
                         self._create_pokemon(unique_id=3, favorite=True),
                         self._create_pokemon(unique_id=4, favorite=False),
                         self._create_pokemon(unique_id=5, favorite=True),
                         self._create_pokemon(unique_id=6, favorite=False)]

        result_dict = transfer_plugin.filter_favorited_pokemon(bot=bot, transfer_list=transfer_list)
        filtered_list = result_dict["transfer_list"]
        assert len(filtered_list) == 2
        assert filtered_list[0].unique_id == 4
        assert filtered_list[1].unique_id == 6
        assert result_dict["filter_list"][0] == "excluding favorited Pokemon"

        transfer_list = [self._create_pokemon(favorite=False)]
        result_dict = transfer_plugin.filter_favorited_pokemon(bot=bot, transfer_list=transfer_list)
        assert len(result_dict["transfer_list"]) == 1
        assert len(result_dict["filter_list"]) == 0

        self.set_empty_inventory(bot)
        assert transfer_plugin.filter_favorited_pokemon(bot=bot) is False

    # TODO: Fix test to use proper config with DI
    def test_ignore_list_filter(self):
        event_manager = EventManager()
        logger = Mock()
        logger.log = Mock()
        transfer_plugin = TransferPokemon(
            {
                'transfer_on_start': False,
                'use_always_keep_filter': True,
                'use_cp_iv_filter': False,
                'always_keep': {
                    'Bulbasaur': True,
                    'Ivysaur': True,
                    'Venusaur': True,
                }
            },
            event_manager,
            logger
        )

        bot = create_mock_bot()

        transfer_list = [self._create_pokemon(unique_id=1, species_id=1),
                         self._create_pokemon(unique_id=2, species_id=5),
                         self._create_pokemon(unique_id=3, species_id=2),
                         self._create_pokemon(unique_id=4, species_id=4),
                         self._create_pokemon(unique_id=5, species_id=3),
                         self._create_pokemon(unique_id=6, species_id=1),
                         self._create_pokemon(unique_id=7, species_id=5)]

        result_dict = transfer_plugin.filter_pokemon_by_ignore_list(bot=bot, transfer_list=transfer_list)
        filtered_list = result_dict["transfer_list"]
        assert len(filtered_list) == 3
        assert filtered_list[0].unique_id == 2
        assert filtered_list[1].unique_id == 4
        assert filtered_list[2].unique_id == 7
        assert "Bulbasaurs" in result_dict["filter_list"][0]
        assert "Ivysaurs" in result_dict["filter_list"][0]
        assert "Venusaurs" in result_dict["filter_list"][0]

        transfer_list = [self._create_pokemon(species_id=42)]
        result_dict = transfer_plugin.filter_pokemon_by_ignore_list(bot=bot, transfer_list=transfer_list)
        assert len(result_dict["transfer_list"]) == 1
        assert len(result_dict["filter_list"]) == 0

        transfer_list = [self._create_pokemon(species_id=1)]
        result_dict = transfer_plugin.filter_pokemon_by_ignore_list(bot=bot, transfer_list=transfer_list)
        assert len(result_dict["transfer_list"]) == 0
        assert result_dict["filter_list"][0] == "excluding Bulbasaurs"

        self.set_empty_inventory(bot)
        assert transfer_plugin.filter_pokemon_by_ignore_list(bot=bot) is False

    @staticmethod
    def _create_pokemon(unique_id=0, species_id=1, cp=1.0, iv=1.0, favorite=False, deployed=False):
        return Pokemon({
            "id": unique_id,
            "pokemon_id": species_id,
            "cp": cp,
            "individual_attack": int(15 * iv),
            "individual_defense": int(15 * iv),
            "individual_stamina": int(15 * iv),
            "favorite": 1 if favorite else 0,
            "deployed_fort_id": "123456" if deployed else None
        })

    @staticmethod
    def set_empty_inventory(bot):
        pgo = bot.api_wrapper._api  # pylint: disable=protected-access

        pgo.set_response("get_player", {})
        pgo.set_response("get_inventory", {})
