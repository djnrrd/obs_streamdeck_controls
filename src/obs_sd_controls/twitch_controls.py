from irc.bot import SingleServerIRCBot
from . import conf


class TwitchSafetyBot(SingleServerIRCBot):
    """A simple bot that logs into the twitch user's own channel to run a
    batch of commands before logging out again.

    :param nickname: The user's twitch logon
    :type nickname: str
    :param token: The user's OAUTH token
    :type token: str
    :param enabled: If this safety mode is enabled
    :type enabled: bool
    :param emote_mode: If Emote Only chat is part of the requested safety
        mode
    :type emote_mode: bool
    :param method: The preferred chat lockdown method
    :type method: str
    :param follow_time: If the lockdown method is Followers only, the length
        of follow time allowed before a user can chat
    :type follow_time: str
    :cvar VERSION: IRC Bot Version
    :cvar channel: The user's chat channel
    :cvar enabled: If this safety mode is enabled
    :cvar emote_mode: If Emote Only chat is part of the requested safety mode
    :cvar method: The preferred chat lockdown method
    :cvar follow_time: If the lockdown method is Followers only, the length
        of follow time allowed before a user can chat
    """
    VERSION = conf.VERSION

    def __init__(self, nickname, token, enabled, emote_mode, method,
                 follow_time):
        token = f"oauth:{token}"
        super().__init__([('irc.twitch.tv', 6667, token)], nickname,
                         nickname)
        self.channel = nickname
        self.enabled = enabled
        self.emote_mode = emote_mode
        self.method = method
        self.follow_time = follow_time

    def on_welcome(self, connection, event):
        """Event handler to make sure the extra twitch capabilities are
        requested and to join the user's channel
        """
        connection.cap('REQ', ':twitch.tv/membership')
        connection.cap('REQ', ':twitch.tv/tags')
        connection.cap('REQ', ':twitch.tv/commands')
        connection.join(self.channel)

    def on_roomstate(self, connection, event):
        """After receiving the ROOMSTATE tags from Twitch IRC, toggle between
        the requested safety modes before gracefully logging out of IRC"""
        if self.enabled:
            # We are performing a safety action
            room_tags = dict([(x['key'], x['value']) for x in event.tags])
            # check if emote mode was selected
            if self.emote_mode:
                # Check if emote only mode is currently enabled, use eval
                # because it's a text '0' or '1' returned
                if eval(room_tags['emote-only']):
                    connection.privmsg(event.target, '/emoteonlyoff')
                else:
                    connection.privmsg(event.target, '/emoteonly')
            # Check which method we're locking down to
            if self.method == 'FOLLOWER':
                # If follower mode is enabled we should have a positive
                # number for the value. Use eval because it's read as a text
                # field
                if eval(room_tags['followers-only']) > 0:
                    connection.privmsg(event.target, '/followersoff')
                else:
                    connection.privmsg(event.target, f"/followers "
                                                     f"{self.follow_time}")
            elif self.method == 'SUBSCRIBER':
                # Check if subscriber only mode is currently enabled, use eval
                # because it's a text '0' or '1' returned
                if eval(room_tags['subs-only']):
                    connection.privmsg(event.target, '/subscribersoff')
                else:
                    connection.privmsg(event.target, '/subscribers')
        self.die('Chat safety measures enabled')


class TwitchLiveSafetyBot(TwitchSafetyBot):
    """A simple bot that logs into the twitch user's own channel to run a
    batch of commands before logging out again.  This bot is for use during
    live streams.

    :param nickname: The user's twitch logon
    :type nickname: str
    :param token: The user's OAUTH token
    :type token: str
    :param enabled: If this safety mode is enabled
    :type enabled: bool
    :param emote_mode: If Emote Only chat is part of the requested safety
        mode
    :type emote_mode: bool
    :param method: The preferred chat lockdown method
    :type method: str
    :param follow_time: If the lockdown method is Followers only,
        the length of follow time allowed before a user can chat
    :type follow_time: str
    :param advert: If a 1m advert should currently be played
    :type advert: bool
    :param marker: If a marker should be placed
    :type marker: bool
    :cvar channel: The user's chat channel
    :cvar enabled: If this safety mode is enabled
    :cvar emote_mode: If Emote Only chat is part of the requested safety
        mode
    :cvar method: The preferred chat lockdown method
    :cvar follow_time: If the lockdown method is Followers only, the length
        of follow time allowed before a user can chat
    :cvar advert: If a 1m advert should currently be played
    :cvar marker: If a marker should be placed
    """

    def __init__(self, nickname, token, enabled, emote_mode, method,
                 follow_time, advert, clear_chat):
        super().__init__(nickname, token, enabled, emote_mode, method,
                         follow_time)
        self.advert = advert
        self.clear_chat = clear_chat

    def on_roomstate(self, connection, event):
        """Override the parent event handler to run the live related features
        before the chat modes.
        """
        if self.enabled:
            room_tags = dict([(x['key'], x['value']) for x in event.tags])
            if all([eval(room_tags['followers-only']) < 0,
                    not eval(room_tags['subs-only'])]):
                if self.advert:
                    connection.privmsg(event.target, '/commercial 60')
                if self.clear_chat:
                    connection.privmsg(event.target, '/clear')
        super().on_roomstate(connection, event)


def start_stop_safety(username, token, enabled, emote_mode, method,
                      follow_time):
    safety_bot = TwitchSafetyBot(username, token, enabled, emote_mode, method,
                                 follow_time)
    safety_bot.start()


def live_safety(username, token, enabled, emote_mode, method, follow_time,
                advert, clear_chat):
    safety_bot = TwitchLiveSafetyBot(username, token, enabled, emote_mode,
                                     method, follow_time, advert, clear_chat)
    safety_bot.start()
