from irc.bot import SingleServerIRCBot
import logging
import sys
from time import sleep


def _get_logger():

    logger_name = 'batch_bot'
    logger_level = logging.DEBUG
    log_line_format = '%(asctime)s | %(name)s - %(levelname)s : %(message)s'
    log_line_date_format = '%Y-%m-%dT%H:%M:%SZ'
    logger_ = logging.getLogger()
    logger_.setLevel(logger_level)
    logging_handler = logging.StreamHandler(stream=sys.stdout)
    logging_handler.setLevel(logger_level)
    logging_formatter = logging.Formatter(log_line_format,
                                          datefmt=log_line_date_format)
    logging_handler.setFormatter(logging_formatter)
    logger_.addHandler(logging_handler)
    return logger_


logger = _get_logger()


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
        # You must request specific capabilities before you can use them
        connection.cap('REQ', ':twitch.tv/membership')
        connection.cap('REQ', ':twitch.tv/tags')
        connection.cap('REQ', ':twitch.tv/commands')
        connection.join(self.channel)
        connection.privmsg(event.target, 'I am here!')
        # self.die('Locked down chat')


    def on_roomstate(self, connection, event):
        logger.debug('roomstate event handler')
        for room_option in event.tags:
            if room_option['key'] == 'emote-only':
                emote = room_option['value']
            if room_option['key'] == 'followers-only':
                followers = room_option['value']
            if room_option['key'] == 'subs-only':
                subs = room_option['value']
        logger.debug('emote - %s : followers - %s : subs - %s', emote,
                     followers, subs)


def start_stop_safety(username, token):
    batch_bot = TwitchBatchBot(username, token)
    batch_bot.start()
