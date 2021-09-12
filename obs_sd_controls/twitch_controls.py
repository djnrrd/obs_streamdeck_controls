from irc.bot import SingleServerIRCBot


class TwitchBatchBot(SingleServerIRCBot):

    VERSION = '0.2.0'

    def __init__(self, nickname, token):
        """A simple bot that logs into the twitch user's own channel to run a
        batch of commands before logging out again.

        :param nickname: The user's twitch logon
        :type nickname: str
        :param token: The user's OAUTH token
        :type token: str
        :cvar channel: The user's chat channel
        """
        token = f"oauth:{token}"
        super().__init__([('irc.twitch.tv', 6667, token)], nickname,
                         nickname)
        self.channel = nickname

    def on_welcome(self, connection, event):
        connection.join(self.channel)
        connection.privmsg(event.target, '/followers 1d')
        self.die('Locked down chat')


def start_stop_safety(username, token):
    batch_bot = TwitchBatchBot(username, token)
    batch_bot.start()
