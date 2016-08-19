# -*- coding: utf-8 -*-
from app import Plugin
from app import kernel

@kernel.container.register('collect_rewards', ['@pokemongo_bot', '@api_wrapper', '@event_manager', '@logger'], tags=['plugin'])
class CollectRewards(Plugin):
    """
    # ----
    # Plugin: Reward Collector
    # Desription: Will collect level up rewards. It will also print a "level up" notice along with the loot.
    # ----
    """
    xp_current = None
    xp_next_level = None
    xp_to_next_level = None
    level_current = None
    level_previous = None

    def __init__(self, pokemongo_bot, api_wrapper, event_manager, logger):
        self.pokemongo_bot = pokemongo_bot
        self.api_wrapper = api_wrapper
        self.event_manager = event_manager
        self.set_logger(logger, 'RewardCollector')

        # register events
        self.event_manager.add_listener('service_player_updated', self.service_player_updated, priority=0)

    # pylint: disable=unused-argument
    def service_player_updated(self, event, data):
        # cancel if no data is provided
        if data is None:
            return

        # get current player info (not calling player, cause that will cause an infinite loop)
        # pylint: disable=protected-access
        player = data._player

        # store it locally
        CollectRewards.xp_current = int(player.experience)
        CollectRewards.xp_next_level = int(player.next_level_xp)
        CollectRewards.xp_to_next_level = int(player.next_level_xp) - int(player.experience)
        CollectRewards.level_current = int(player.level)

        # check for rewards on startup
        if CollectRewards.level_previous is None:
            # try to claim rewards
            self._claim_levelup_reward()

        # check for level up
        if int(player.level) > CollectRewards.level_previous:
            # try to claim rewards
            self._claim_levelup_reward()

    def _claim_levelup_reward(self):
        fire_event = False
        # level up notice
        if CollectRewards.level_previous is None:
            self.log('Running initial reward check ...', color='yellow')
        else:
            self.log('Congratulations! You have reached level {}'.format(CollectRewards.level_current), color='green')
            fire_event = True

        # set previous level to current level
        CollectRewards.level_previous = CollectRewards.level_current

        # api call - request the rewards
        # Example : {'items_awarded': [{'item_id': 1, 'item_count': 15}, {'item_id': 1, 'item_count': 15}], 'result': 1}
        response_dict = self.api_wrapper.level_up_rewards(level=CollectRewards.level_current).call()
        reward_dict = response_dict['LEVEL_UP_REWARDS']

        # check if there is a reward to give out
        if reward_dict['result'] == 1:
            self.log("Loot: ", "green")

            # no reward for level 1 (will return result 1 without items_awarded)
            if 'items_awarded' in reward_dict.keys():
                # log loot
                for item in reward_dict['items_awarded']:
                    item_type = item['item_id']
                    item_name = self.pokemongo_bot.item_list[item_type]
                    item_count = item['item_count']
                    self.log("+ {} {}{}".format(item_count, item_name, "s" if item_count > 1 else ""), "green")

        # fire event
        if fire_event:
            self.event_manager.fire('player_level_up', level=CollectRewards.level_current)
