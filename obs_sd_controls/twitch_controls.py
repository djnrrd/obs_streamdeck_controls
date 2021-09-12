from irc.bot import SingleServerIRCBot


class TwitchBatchBot(SingleServerIRCBot):

    VERSION = '0.2.0'

    def __init__(self, nickname, token):
        token = f"oauth:{token}"
        super().__init__([('irc.twitch.tv', 6667, token)], nickname,
                         nickname)
        self.channel = nickname
        self.viewers = []

    def on_welcome(self, connection, event):
        connection.join(self.channel)
        connection.privmsg(event.target, '/followers 1d')
        self.die('Locked down chat')

    def on_disconnect(self, connection, event):
        pass

    @staticmethod
    def _parse_nickname_from_twitch_user_id(user_id):
        # nickname!username@nickname.tmi.twitch.tv
        return user_id.split('!', 1)[0]


def start_stop_safety(username, token):
    batch_bot = TwitchBatchBot(username, token)
    batch_bot.start()
