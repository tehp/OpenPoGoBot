class AccountBannedException(Exception):

    def __init__(self, message=None):
        if message is None:
            message = "[API] Status code 3 received. This may mean that your account is permanently banned. See https://www.reddit.com/r/pokemongodev/comments/4xkqmq/new_ban_types_and_their_causes/ for details."
        super(AccountBannedException, self).__init__(message)
