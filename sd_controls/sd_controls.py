import asyncio
import simpleobsws
from configparser import ConfigParser
from appdirs import user_config_dir
from os import path


def _read_config():
    """Read the config file from the user config directory and return the
    ConfigParser obect

    :return: The ConfigParser object
    :rtype: ConfigParser
    """



async def _ws_toggle_mute(source):
    """Use the OBS-Websocket to mute/unmute an audio source

    :param source: The OBS audio source to mute/unmute
    :type source: str
    """
    # Make the connection to obs-websocket
    await WS.connect()
    data = {'source': source}
    await WS.call('ToggleMute', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()


async def _ws_get_scene_list():
    """Use the OBS-Websocket to get the list of scenes

    :return: The currently active scene and an ordered list of all scenes
        configured in OBS
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await WS.connect()
    result = await WS.call('GetSceneList')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()
    return result


async def _ws_set_scene(scene):
    """Use the OBS-Websocket to set the current scene

    :param scene: The name of the scene in OBS to make active
    :type scene: str
    """
    # Make the connection to obs-websocket
    await WS.connect()
    data = {'scene-name': scene}
    await WS.call('SetCurrentScene', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()


async def _ws_start_stop_stream():
    """Use the OBS-Websocket to start or stop streaming
    """
    # Make the connection to obs-websocket
    await WS.connect()
    await WS.call('StartStopStreaming')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()


async def _ws_get_source_settings(source):
    """Use the OBS-Websocket to get the settings for a source

    :param source: The OBS source to get the settings for
    :type source: str
    :return: Details on the source name, type and the settings for the source
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await WS.connect()
    data = {'sourceName': source}
    result = await WS.call('GetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()
    return result


async def _ws_set_source_settings(source, settings):
    """Use the OBS-Websocket to set new settings for a source

    :param source: The OBS source to update
    :type source: str
    :param settings: The updated settings to apply to the source in the same
        format as the sourceSettings section returned from
        _ws_get_source_settings
    :type settings: dict
    :return: Details on the source name, type and the updated settings for the
        source
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await WS.connect()
    data = {'sourceName': source, 'sourceSettings': settings}
    result = await WS.call('SetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await WS.disconnect()
    return result


def mute_desktop_audio():
    """Mute/Unmute the Desktop audio source as configured in sd_controls.ini
    """
    LOOP.run_until_complete(_ws_toggle_mute(CONFIG['obs']['desktop_source']))


def mute_mic_audio():
    """Mute/Unmute the Microphone audio source as configured in sd_controls.ini
    """
    LOOP.run_until_complete(_ws_toggle_mute(CONFIG['obs']['mic_source']))


def mute_both_audio():
    """Mute/Unmute both Desktop and Microphone audio sources as configured in
    sd_controls.ini
    """
    for source in (CONFIG['obs']['mic_source'],
                   CONFIG['obs']['desktop_source']):
        LOOP.run_until_complete(_ws_toggle_mute(source))


def set_scene(scene_number):
    """Set the active scene in OBS using the number of the scene as counted
    from the top down of the scene list in OBS

    :param scene_number: The scene number to make active
    :type scene_number: int
    """
    scene_list = LOOP.run_until_complete(_ws_get_scene_list())
    # Adjust for zero indexing
    scene_number = scene_number - 1
    new_scene = scene_list['scenes'][scene_number]['name']
    LOOP.run_until_complete(_ws_set_scene(new_scene))


def start_stop_stream():
    """Start/Stop the stream"""
    LOOP.run_until_complete(_ws_start_stop_stream())


def panic_button():
    """Sadly, people are performing "hate raids" on twitch, raiding channels
    and getting bot accounts to follow the streamer and spam chat with
    hateful messages.

    The follows will cause sound alert overlays to queue up notifications,
    so this function will disable and re-enable those overlays as configured
    in sd_controls.ini

    TODO Integrate with twitch APIs to set chat to "Subscriber only mode"
    or "Followers only mode" (based on follow duration) to block hateful
    messages in chat.

    :raises ValueError: If there is a conflict between either the saved URL for
        the source, or the invalid.lan address that temporarily overwrites
        the source's URL.
    """
    # Loop through configured alert sources
    for source in CONFIG['obs']['alert_sources'].split(':'):
        # Get the current settings for the alert source.
        settings = LOOP.run_until_complete(_ws_get_source_settings(source))
        settings = settings['sourceSettings']
        # check if the source url is saved to the ini file, if not assume
        # this is the first time we've run this and save it
        if not CONFIG.has_option('obs_browser_sources', source):
            CONFIG['obs_browser_sources'][source] = settings['url']
            with open(CONFIG_FILE, 'w') as f:
                CONFIG.write(f)
        # Swap Browser source between saved URl and invalid.lan
        if settings['url'] == CONFIG['obs_browser_sources'][source]:
            settings['url'] = 'http://invalid.lan'
        elif settings['url'] == 'http://invalid.lan':
            settings['url'] = CONFIG['obs_browser_sources'][source]
        else:
            raise ValueError('Browser source matches neither the saved value '
                             'in the ini file or \'http://invalid.lan/\'')
        # Swap reroute_audio settings to make sure the audio for the browser
        # source is routed through the OBS audio mixer and can be muted,
        # instead of through the default Desktop audio source
        if settings['reroute_audio']:
            settings['reroute_audio'] = False
        else:
            settings['reroute_audio'] = True
        # Update the settings and mute the sources.
        LOOP.run_until_complete(_ws_set_source_settings(source, settings))
        LOOP.run_until_complete(_ws_toggle_mute(source))

# Globals for sd_controls and cli_tools
CONFIG_DIR = user_config_dir('obs-streamdeck-ctl')
CONFIG_FILE = path.join(CONFIG_DIR, 'obs-streamdeck.ini')
CONFIG = ConfigParser()
CONFIG.read(CONFIG_FILE)

if CONFIG.has_option('obs', 'obsws_password'):
    WS = simpleobsws.obsws(password=CONFIG['obs']['obsws_password'])
else:
    WS = simpleobsws.obsws()
LOOP = asyncio.get_event_loop()
